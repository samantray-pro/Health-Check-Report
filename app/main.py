import io
import csv
import socket
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.database import get_db, init_db, seed_sample_data_if_empty
from app.models import ProfileCreate, ConfirmReportPayload
from app.ocr_engine import extract_text_from_file
from app.parser import parse_lab_data, BIOMARKER_DICTIONARY, get_test_category
from app import ai_router

app = FastAPI(title="Local Health Checkup Tracker", description="Privacy-focused, offline-first health checkup tracker")

# Enable CORS for local network flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_router.router, prefix="/api/ai", tags=["AI"])

UPLOAD_DIR = Path("app/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

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

@app.delete("/api/profiles/{profile_id}")
def delete_profile(profile_id: int):
    with get_db() as db:
        db.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
        db.commit()
        return {"status": "success", "message": "Profile deleted"}

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

    with get_db() as db:
        # Record report entry
        file_type = "pdf" if payload.filename.lower().endswith(".pdf") else "image"
        cur = db.execute(
            "INSERT INTO reports (profile_id, filename, file_path, file_type, report_date) VALUES (?, ?, ?, ?, ?)",
            (profile_id, payload.filename or "Manual", payload.file_path or "", file_type, payload.test_date)
        )
        report_id = cur.lastrowid

        for r in payload.records:
            db.execute("""
                INSERT INTO test_records 
                (profile_id, report_id, test_name, raw_test_name, value, value_str, unit, reference_range, flag, test_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                profile_id,
                report_id,
                r.test_name.strip(),
                r.raw_test_name or r.test_name.strip(),
                r.value,
                str(r.value),
                r.unit or "",
                r.reference_range or "",
                r.flag or "NORMAL",
                payload.test_date
            ))
        db.commit()

    return {"status": "success", "saved_count": len(payload.records)}

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

@app.delete("/api/records/{record_id}")
def delete_record(record_id: int):
    with get_db() as db:
        db.execute("DELETE FROM test_records WHERE id = ?", (record_id,))
        db.commit()
        return {"status": "success"}

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
