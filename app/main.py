import io
import csv
import socket
import logging
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.database import get_db, init_db, seed_sample_data_if_empty
from app.models import ProfileCreate, ConfirmReportPayload, UpdateRecordPayload, RenameTestPayload
from app.ocr_engine import extract_text_from_file
from app.parser import parse_lab_data, BIOMARKER_DICTIONARY, get_test_category, get_test_panel, determine_clinical_flag, resolve_biomarker_meta
from app import ai_router

logger = logging.getLogger("health_tracker")

app = FastAPI(title="Local Health Checkup Tracker", description="Privacy-focused, offline-first health checkup tracker")

# Enable CORS for local network flexibility (no cookies/auth used, so no credentials needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_router.router, prefix="/api/ai", tags=["AI"])

UPLOAD_DIR = Path("app/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR_RESOLVED = UPLOAD_DIR.resolve()

def safe_upload_path(file_path: str) -> Path | None:
    """Resolves a stored file_path and returns it only if it lives inside UPLOAD_DIR, else None."""
    if not file_path:
        return None
    try:
        resolved = Path(file_path).resolve()
        resolved.relative_to(UPLOAD_DIR_RESOLVED)
        return resolved
    except (OSError, ValueError):
        return None

def get_lan_ip():
    """Detects the machine's local network IP address (e.g., 192.168.x.x)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

@app.on_event("startup")
def startup():
    init_db()
    seed_sample_data_if_empty()

# --- System & Network Endpoints ---
@app.get("/api/system/info")
def get_system_info():
    lan_ip = get_lan_ip()
    return {
        "lan_ip": lan_ip,
        "port": 8000,
        "local_url": "http://localhost:8000",
        "network_url": f"http://{lan_ip}:8000"
    }

# --- Profiles Endpoints ---
@app.get("/api/profiles")
def list_profiles():
    with get_db() as db:
        rows = db.execute("""
            SELECT p.id, p.name, p.age, p.gender, p.health_issues, p.created_at,
                   COUNT(DISTINCT t.test_name) as unique_tests_count,
                   MAX(t.test_date) as last_checkup_date
            FROM profiles p
            LEFT JOIN test_records t ON p.id = t.profile_id
            GROUP BY p.id
            ORDER BY p.id ASC
        """).fetchall()
        return [dict(r) for r in rows]

@app.post("/api/profiles")
def create_profile(profile: ProfileCreate):
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO profiles (name, age, gender, health_issues) VALUES (?, ?, ?, ?)",
            (profile.name.strip(), profile.age, profile.gender, (profile.health_issues or "").strip())
        )
        db.commit()
        return {"id": cur.lastrowid, "name": profile.name}

# --- Biomarkers Dictionary Reference ---
@app.get("/api/biomarkers")
def get_biomarkers():
    """Returns the list of known medical biomarkers with units and normal ranges."""
    unique_biomarkers = {}
    for meta in BIOMARKER_DICTIONARY.values():
        unique_biomarkers[meta["name"]] = meta
    return list(unique_biomarkers.values())

# --- Upload & Extraction Endpoints ---
@app.post("/api/profiles/{profile_id}/upload")
async def upload_report(profile_id: int, file: UploadFile = File(...)):
    # Validate profile existence
    with get_db() as db:
        profile = db.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

    # Secure local file write
    safe_filename = f"{profile_id}_{Path(file.filename).name}"
    file_path = UPLOAD_DIR / safe_filename

    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Execute Hybrid Extraction (Digital PDF text or Tesseract OCR)
    raw_text = extract_text_from_file(file_path)
    extracted_date, detected_tests = parse_lab_data(raw_text)

    return {
        "filename": file.filename,
        "file_path": str(file_path),
        "extracted_date": extracted_date,
        "detected_tests": detected_tests,
        "raw_text_length": len(raw_text),
        "raw_text_preview": raw_text[:800] if raw_text else "(No text extracted)"
    }

@app.post("/api/profiles/{profile_id}/confirm")
def confirm_records(profile_id: int, payload: ConfirmReportPayload):
    """Saves verified test records after user review."""
    if not payload.records:
        raise HTTPException(status_code=400, detail="No test records provided to save")

    safe_file_path = str(safe_upload_path(payload.file_path)) if payload.file_path else ""

    with get_db() as db:
        # Calculate distinct test panels and total parameters count
        distinct_panels = set()
        for r in payload.records:
            panel_val = r.panel or get_test_panel(r.test_name, r.category)
            distinct_panels.add(panel_val)

        panel_count = len(distinct_panels)
        parameter_count = len(payload.records)

        # Record report entry
        file_type = "pdf" if payload.filename.lower().endswith(".pdf") else "image"
        cur = db.execute(
            "INSERT INTO reports (profile_id, filename, file_path, file_type, report_date, panel_count, parameter_count) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (profile_id, payload.filename or "Manual", safe_file_path, file_type, payload.test_date, panel_count, parameter_count)
        )
        report_id = cur.lastrowid

        for r in payload.records:
            dict_meta = resolve_biomarker_meta(r.test_name)

            computed_flag = determine_clinical_flag(r.value, r.reference_range or "", dict_meta)
            saved_flag = computed_flag if computed_flag in ("HIGH", "LOW", "NORMAL", "BORDERLINE") else (r.flag or "NORMAL")

            assigned_category = r.category or (dict_meta.get("category") if dict_meta else get_test_category(r.test_name))
            assigned_panel = r.panel or (dict_meta.get("panel") if (dict_meta and "panel" in dict_meta) else get_test_panel(r.test_name, assigned_category))

            db.execute("""
                INSERT INTO test_records 
                (profile_id, report_id, test_name, raw_test_name, panel, category, value, value_str, unit, reference_range, flag, test_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                profile_id,
                report_id,
                r.test_name.strip(),
                r.raw_test_name or r.test_name.strip(),
                assigned_panel,
                assigned_category,
                r.value,
                r.value_str if r.value_str else str(r.value),
                r.unit or "",
                r.reference_range or "",
                saved_flag,
                payload.test_date
            ))
        db.commit()

    return {
        "status": "success",
        "saved_count": len(payload.records),
        "panel_count": panel_count,
        "parameter_count": parameter_count
    }

# --- BI & Panel Analytics Endpoint ---
@app.get("/api/profiles/{profile_id}/bi/panels")
def get_profile_bi_panels(profile_id: int):
    """Returns panel distribution and parameter metrics for BI reporting."""
    with get_db() as db:
        rows = db.execute("""
            SELECT panel, category,
                   COUNT(*) as total_readings,
                   COUNT(DISTINCT test_name) as parameter_count,
                   SUM(CASE WHEN flag IN ('HIGH', 'LOW', 'BORDERLINE', 'ABNORMAL') THEN 1 ELSE 0 END) as abnormal_count,
                   MAX(test_date) as last_test_date
            FROM test_records
            WHERE profile_id = ?
            GROUP BY panel
            ORDER BY parameter_count DESC, panel ASC
        """, (profile_id,)).fetchall()
        return [dict(r) for r in rows]

# --- Dashboard & Trend Analytics Endpoints ---
@app.get("/api/profiles/{profile_id}/dashboard")
def get_profile_dashboard(profile_id: int):
    """Returns overview metrics, recent tests, and per-test last 5 readings for trend curves."""
    with get_db() as db:
        profile = db.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Get all distinct tests recorded for this profile
        tests = db.execute("""
            SELECT test_name, unit, reference_range, MAX(test_date) as last_date
            FROM test_records
            WHERE profile_id = ?
            GROUP BY test_name
            ORDER BY last_date DESC, test_name ASC
        """, (profile_id,)).fetchall()

        test_cards = []
        abnormal_count = 0
        total_readings = 0

        for t in tests:
            # Retrieve all historical readings for this test sorted chronologically
            history = db.execute("""
                SELECT id, value, value_str, unit, reference_range, flag, test_date
                FROM test_records
                WHERE profile_id = ? AND test_name = ?
                ORDER BY test_date ASC, id ASC
            """, (profile_id, t["test_name"])).fetchall()

            history_list = [dict(h) for h in history]
            total_readings += len(history_list)
            last_5 = history_list[-5:]
            latest = last_5[-1] if last_5 else None

            if latest and latest["flag"] in ("HIGH", "LOW", "BORDERLINE"):
                abnormal_count += 1

            # Determine trend direction (last reading vs second-to-last reading)
            trend_direction = "stable"
            change_str = "0"
            if len(last_5) >= 2:
                prev_val = last_5[-2]["value"]
                curr_val = last_5[-1]["value"]
                diff = curr_val - prev_val
                if diff > 0.01:
                    trend_direction = "up"
                    change_str = f"+{diff:.2f}".rstrip('0').rstrip('.')
                elif diff < -0.01:
                    trend_direction = "down"
                    change_str = f"{diff:.2f}".rstrip('0').rstrip('.')

            category = get_test_category(t["test_name"])

            test_cards.append({
                "test_name": t["test_name"],
                "category": category,
                "unit": latest["unit"] if latest else t["unit"],
                "reference_range": latest["reference_range"] if latest else t["reference_range"],
                "latest_value": latest["value"] if latest else None,
                "latest_value_str": latest.get("value_str") if latest else None,
                "latest_flag": latest["flag"] if latest else "NORMAL",
                "latest_date": latest["test_date"] if latest else None,
                "trend_direction": trend_direction,
                "change_str": change_str,
                "last_5_records": last_5,
                "total_history_count": len(history_list)
            })

        # Calculate category distribution and abnormal counts
        category_map = {}
        for card in test_cards:
            c_name = card["category"]
            if c_name not in category_map:
                category_map[c_name] = {"name": c_name, "count": 0, "abnormal_count": 0}
            category_map[c_name]["count"] += 1
            if card["latest_flag"] in ("HIGH", "LOW", "BORDERLINE"):
                category_map[c_name]["abnormal_count"] += 1

        panel_order = [
            "Diabetes & Glycemic",
            "Complete Blood Count (CBC)",
            "Lipid Profile",
            "Liver Function (LFT)",
            "Kidney Function (KFT)",
            "Thyroid Profile",
            "Vitamins & Minerals",
            "Iron Studies",
            "Cardiac & Inflammation",
            "Hormones & Immunology",
            "General / Other"
        ]
        sorted_categories = sorted(
            category_map.values(),
            key=lambda x: panel_order.index(x["name"]) if x["name"] in panel_order else 99
        )

        return {
            "profile": dict(profile),
            "stats": {
                "unique_tests": len(tests),
                "total_readings": total_readings,
                "abnormal_flags": abnormal_count,
                "last_checkup": tests[0]["last_date"] if tests else None
            },
            "categories": sorted_categories,
            "cards": test_cards
        }

@app.get("/api/profiles/{profile_id}/test-detail")
def get_test_detail(profile_id: int, test_name: str = Query(...)):
    """Returns complete historical records for a single test."""
    with get_db() as db:
        records = db.execute("""
            SELECT id, value, value_str, unit, reference_range, flag, test_date, created_at
            FROM test_records
            WHERE profile_id = ? AND test_name = ?
            ORDER BY test_date ASC, id ASC
        """, (profile_id, test_name)).fetchall()

        return {
            "test_name": test_name,
            "records": [dict(r) for r in records]
        }

@app.post("/api/profiles/{profile_id}/tests/rename")
def rename_test(profile_id: int, payload: RenameTestPayload):
    """Renames every record of one test for a profile. Renaming to an existing test's name
    merges the two on the dashboard, since cards are grouped by exact test_name."""
    new_name = payload.new_name.strip()
    if not new_name:
        raise HTTPException(status_code=400, detail="New name cannot be empty")

    dict_meta = resolve_biomarker_meta(new_name)
    category = dict_meta.get("category") if dict_meta else get_test_category(new_name)
    panel = dict_meta.get("panel") if (dict_meta and "panel" in dict_meta) else get_test_panel(new_name, category)

    with get_db() as db:
        cur = db.execute(
            "UPDATE test_records SET test_name = ?, category = ?, panel = ? WHERE profile_id = ? AND test_name = ?",
            (new_name, category, panel, profile_id, payload.old_name)
        )
        db.commit()
        return {"status": "success", "updated_records": cur.rowcount, "new_name": new_name}

@app.put("/api/records/{record_id}")
def update_record(record_id: int, payload: UpdateRecordPayload):
    """Updates the value and/or date of a single saved test reading."""
    with get_db() as db:
        row = db.execute("SELECT test_name, reference_range FROM test_records WHERE id = ?", (record_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Record not found")

        dict_meta = resolve_biomarker_meta(row["test_name"])
        flag = determine_clinical_flag(payload.value, row["reference_range"] or "", dict_meta)

        db.execute(
            "UPDATE test_records SET value = ?, value_str = ?, test_date = ?, flag = ? WHERE id = ?",
            (payload.value, payload.value_str or str(payload.value), payload.test_date, flag, record_id)
        )
        db.commit()
        return {"status": "success", "flag": flag}

@app.delete("/api/records/{record_id}")
def delete_record(record_id: int):
    with get_db() as db:
        db.execute("DELETE FROM test_records WHERE id = ?", (record_id,))
        db.commit()
        return {"status": "success"}

# --- Checkups & Data Deletion Endpoints ---
@app.get("/api/profiles/{profile_id}/checkups")
def get_profile_checkups(profile_id: int):
    """Returns checkup dates for a profile with record counts and attached report information."""
    with get_db() as db:
        checkups = db.execute("""
            SELECT 
                tr.test_date,
                COUNT(tr.id) as records_count,
                MAX(r.id) as report_id,
                MAX(r.filename) as filename,
                MAX(r.file_path) as file_path,
                MAX(r.file_type) as file_type
            FROM test_records tr
            LEFT JOIN reports r ON tr.report_id = r.id
            WHERE tr.profile_id = ?
            GROUP BY tr.test_date
            ORDER BY tr.test_date DESC
        """, (profile_id,)).fetchall()

        return [dict(c) for c in checkups]

@app.delete("/api/profiles/{profile_id}/checkups/{test_date}")
def delete_profile_checkup_date(profile_id: int, test_date: str):
    """Deletes all test records and associated reports/files for a specific checkup date."""
    with get_db() as db:
        # Find distinct reports that originated from this checkup date
        reports = db.execute("""
            SELECT DISTINCT r.id, r.file_path 
            FROM reports r
            JOIN test_records tr ON tr.report_id = r.id
            WHERE tr.profile_id = ? AND tr.test_date = ?
        """, (profile_id, test_date)).fetchall()

        cur = db.execute("DELETE FROM test_records WHERE profile_id = ? AND test_date = ?", (profile_id, test_date))
        deleted_records = cur.rowcount

        # Check if the report has any remaining records; if not, delete the report and physical file
        for rep in reports:
            rem = db.execute("SELECT COUNT(*) as cnt FROM test_records WHERE report_id = ?", (rep["id"],)).fetchone()
            if rem["cnt"] == 0:
                db.execute("DELETE FROM reports WHERE id = ?", (rep["id"],))
                p = safe_upload_path(rep["file_path"])
                if p and p.is_file():
                    try:
                        p.unlink()
                    except OSError as e:
                        logger.warning("Failed to unlink uploaded file %s: %s", p, e)

        db.commit()
        return {"status": "success", "deleted_records": deleted_records, "test_date": test_date}

@app.delete("/api/profiles/{profile_id}/data")
def delete_profile_all_data(profile_id: int):
    """Deletes all test records, reports, and uploaded files for a profile (resets records to 0)."""
    with get_db() as db:
        reports = db.execute("SELECT id, file_path FROM reports WHERE profile_id = ?", (profile_id,)).fetchall()
        for rep in reports:
            p = safe_upload_path(rep["file_path"])
            if p and p.is_file():
                try:
                    p.unlink()
                except OSError as e:
                    logger.warning("Failed to unlink uploaded file %s: %s", p, e)

        cur = db.execute("DELETE FROM test_records WHERE profile_id = ?", (profile_id,))
        deleted_records = cur.rowcount
        db.execute("DELETE FROM reports WHERE profile_id = ?", (profile_id,))
        db.commit()

        return {"status": "success", "deleted_records": deleted_records, "message": "All data cleared for profile"}

@app.delete("/api/profiles/{profile_id}")
def delete_profile(profile_id: int):
    """Deletes the profile and cascades to all its tests, reports, and files."""
    with get_db() as db:
        reports = db.execute("SELECT id, file_path FROM reports WHERE profile_id = ?", (profile_id,)).fetchall()
        for rep in reports:
            p = safe_upload_path(rep["file_path"])
            if p and p.is_file():
                try:
                    p.unlink()
                except OSError as e:
                    logger.warning("Failed to unlink uploaded file %s: %s", p, e)

        db.execute("DELETE FROM test_records WHERE profile_id = ?", (profile_id,))
        db.execute("DELETE FROM reports WHERE profile_id = ?", (profile_id,))
        db.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
        db.commit()

        return {"status": "success", "message": f"Profile {profile_id} and all associated data deleted"}

# --- Export to CSV Endpoint ---
@app.get("/api/profiles/{profile_id}/export-csv")
def export_csv(profile_id: int):
    with get_db() as db:
        profile = db.execute("SELECT name FROM profiles WHERE id = ?", (profile_id,)).fetchone()
        name = profile["name"] if profile else f"profile_{profile_id}"

        records = db.execute("""
            SELECT test_name, test_date, value, unit, reference_range, flag
            FROM test_records
            WHERE profile_id = ?
            ORDER BY test_name ASC, test_date DESC
        """, (profile_id,)).fetchall()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Test Name", "Test Date", "Reading Value", "Unit", "Reference Range", "Clinical Flag"])
        for r in records:
            writer.writerow([r["test_name"], r["test_date"], r["value"], r["unit"], r["reference_range"], r["flag"]])

        output.seek(0)
        safe_name = name.replace(" ", "_").lower()
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="health_report_{safe_name}.csv"'}
        )

# Serve static web assets
STATIC_DIR = Path("static")
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
