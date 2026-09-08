# Architecture & Implementation Blueprint: Local Health Checkup Tracker (Privacy-First)

A local, offline-first health checkup tracking web application with multi-profile support, hybrid OCR report parsing (digital PDF text extraction + Tesseract OCR fallback), longitudinal test comparison (1mg/PharmEasy style last 5 records & sparklines), and local LAN accessibility.

---

## 1. Recommended Architecture & Tech Stack

| Layer | Recommended Choice | Rationale for 2–3 Hour Build & Privacy |
| :--- | :--- | :--- |
| **Backend Framework** | **Python (FastAPI)** | High performance, auto-generates interactive API docs (`/docs`), native async file uploads, and effortless static file serving in a single unified process. |
| **Database** | **SQLite (`health_tracker.db`)** | Embedded, zero-configuration, ACID-compliant, native in Python (`sqlite3`), completely local (single file), and supports instant chronological queries (`ORDER BY test_date DESC LIMIT 5`). Includes 1-click **Export to CSV/Excel** for user data ownership. |
| **OCR & Report Ingestion** | **Hybrid Pipeline (`pdfplumber` + `pytesseract`)** | **Tier 1 (Fast & 100% Accurate)**: Direct digital vector extraction via `pdfplumber` (90%+ of downloaded lab reports from 1mg, Apollo, Lal PathLabs have digital text layers).<br>**Tier 2 (Scanned/Image Fallback)**: Image preprocessing (OpenCV/PIL grayscale + Otsu thresholding) + Tesseract OCR. |
| **Text Parsing & Extraction** | **Regex & Clinical Dictionary Engine** | Normalizes known biomarker names (e.g. "HbA1c", "Fasting Blood Sugar", "Serum Creatinine", "Hemoglobin") and extracts `(Test Name, Value, Unit, Reference Range, Date)`. |
| **Frontend UI/UX** | **Modern Vanilla JS + CSS Grid/Flexbox + Chart.js** | Zero build step (`npm install` / webpack / vite build overhead avoided). Instant hot reload, dark/light clinical theme, mobile-first responsive layout, and interactive trend charts. |
| **Local Network Access** | **Host Binding (`0.0.0.0:8000`)** | Accessible by any smartphone, tablet, or PC on the same Wi-Fi network (`http://<local-ip>:8000`) with auto-detected IP displayed in the UI. |

---

## 2. System Architecture & Data Flow

```
                     ┌─────────────────────────────────────────┐
                     │   Local Network Client (Phone / PC)    │
                     │         http://192.168.x.x:8000         │
                     └────────────────────┬────────────────────┘
                                          │
                                          ▼
                     ┌─────────────────────────────────────────┐
                     │      FastAPI Unified App Server         │
                     │  • Static File Server (HTML/CSS/JS)     │
                     │  • REST Endpoints (/api/profiles, ...)  │
                     └──────┬───────────────────────────┬──────┘
                            │                           │
                            ▼                           ▼
        ┌───────────────────────────────┐   ┌───────────────────────────────┐
        │     OCR & Extraction Engine   │   │      SQLite Local Store       │
        │ • pdfplumber (Digital PDF)    │   │      (health_tracker.db)      │
        │ • pytesseract (Scanned/Image) │   │ • profiles                    │
        │ • Clinical Pattern Extractor  │   │ • reports                     │
        │ • Verification/Edit Step      │   │ • test_records                │
        └───────────────────────────────┘   └───────────────────────────────┘
```

---

## 3. Project Directory Structure

```
Health Check Report/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI server, route definitions, LAN IP detector
│   ├── database.py              # SQLite connection, migrations, query helpers
│   ├── models.py                # Pydantic schemas for request/response validation
│   ├── ocr_engine.py            # Hybrid extraction (pdfplumber + Tesseract OCR)
│   ├── parser.py                # Clinical regex & test-name normalization dictionary
│   └── uploads/                 # Local document storage (gitignored, local only)
│       └── .gitkeep
├── static/
│   ├── css/
│   │   └── style.css            # Modern clinical UI, responsive cards, glassmorphism
│   ├── js/
│   │   └── app.js               # State management (active profile, API calls, routing)
│   └── index.html               # Single-page interface (Profile switch, Upload, Dashboard)
├── sample_reports/              # Sample lab PDF for instant testing
├── test_backend.py              # Backend & parser unit tests
├── test_pdf_upload.py           # End-to-end PDF extraction and API integration test
├── requirements.txt             # Minimal dependencies
├── run.bat                      # 1-click launcher for Windows
├── run.sh                       # 1-click launcher for macOS/Linux
├── README.md                    # Setup and LAN connection guide
└── IMPLEMENTATION_PLAN.md       # Architecture blueprint and roadmap
```

---

## 4. Database Schema (SQLite)

```sql
-- 1. Persona Profiles
CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    gender TEXT NOT NULL,          -- 'Male', 'Female', 'Other'
    health_issues TEXT,            -- Comma-separated or descriptive notes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Uploaded Source Reports
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,       -- 'pdf', 'image'
    report_date DATE,              -- Date extracted from report or specified by user
    extracted_raw_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES profiles (id) ON DELETE CASCADE
);

-- 3. Individual Medical Test Records
CREATE TABLE IF NOT EXISTS test_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    report_id INTEGER,
    test_name TEXT NOT NULL,       -- Normalized test name (e.g., 'Hemoglobin', 'HbA1c')
    raw_test_name TEXT,            -- As extracted from OCR
    value REAL NOT NULL,           -- Numeric reading for trend computation
    value_str TEXT,                -- Original formatted string (e.g., '14.2', '<0.5')
    unit TEXT,                     -- 'g/dL', 'mg/dL', '%', etc.
    reference_range TEXT,          -- e.g., '13.0 - 17.0'
    flag TEXT DEFAULT 'NORMAL',    -- 'NORMAL', 'LOW', 'HIGH', 'CRITICAL'
    test_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES profiles (id) ON DELETE CASCADE,
    FOREIGN KEY (report_id) REFERENCES reports (id) ON DELETE SET NULL
);

-- Indexes for lightning-fast chronological comparison
CREATE INDEX IF NOT EXISTS idx_records_profile_test ON test_records (profile_id, test_name, test_date DESC);
```

---

## 5. Core Code Architecture

### A. Dependencies (`requirements.txt`)
```text
fastapi>=0.110.0
uvicorn[standard]>=0.28.0
python-multipart>=0.0.9
pydantic>=2.6.0
pdfplumber>=0.11.0
pytesseract>=0.3.10
Pillow>=10.2.0
pypdf>=4.0.0
```

### B. Hybrid OCR & Clinical Parser (`app/ocr_engine.py` & `app/parser.py`)
- Standardized dictionary normalizing variations (e.g., "fasting blood glucose", "fbs", "glycated hemoglobin", "hba1c").
- High-efficiency digital PDF vector stream extraction.
- Automatic biological flag classification (`NORMAL`, `HIGH`, `LOW`, `BORDERLINE`).

### C. FastAPI Backend & Database Helpers (`app/main.py`)
- Single unified process serving REST API and responsive frontend.
- Chronological query aggregation (`last_5_records`, delta trends `↑`, `↓`, `Stable`).
- Automatic local LAN IP detection (`http://<lan-ip>:8000`).
- 1-click CSV export endpoint.

---

## 6. UI/UX Design & Layouts (Tata 1mg / PharmEasy Experience)

- **Theme**: Clean Medical Slate & Cyan.
  - Background: `#0B0F19` & `#111827`
  - Primary Brand: `#0284C7` (Sky Blue) & `#0D9488` (Teal)
  - Normal / Optimal: `#10B981` (Emerald)
  - Attention / Borderline: `#F59E0B` (Amber)
  - Critical / High: `#EF4444` (Rose)
- **Top Summary Metrics**: Total tests tracked, data points logged, abnormal flags, last checkup date.
- **Dual View Modes (User Selectable)**:
  - **Grid View (⊞)**: 3-column card grid with big readings, clinical status pills, trend badges, 5-point sparkline canvases, and last 5 checkup chips.
  - **Linear View (☰)**: High-density horizontal row layout with inline metadata, readings, compact sparklines, and quick action buttons for high-efficiency scanning.
- **Dynamic Filter & Search Toolbar**:
  - Live search input matching biomarker name, units, and reference intervals.
  - Status filter pills: `All`, `⚠️ Attention Needed` (Abnormal/High/Low only), `✓ Normal`.
  - Multi-criteria sorting: `Most Recent`, `Attention First`, `Name (A to Z)`, `Name (Z to A)`.
- **Verification & Review Drawer**: Editable tabular review interface prior to committing OCR results.
- **Deep-Dive Timeline**: Full-sized interactive Chart.js line graph and chronological audit table.

---

## 7. Security & Privacy for Local-Only Health Data

1. **Zero External API Calls**: The app runs 100% locally. No telemetry, no cloud OCR endpoints, no analytics scripts.
2. **Network Isolation**: Binds to `0.0.0.0` for local LAN access (home Wi-Fi). Supports `--host 127.0.0.1` for strict localhost-only mode.
3. **Local File Sanitization**: Uploaded files are assigned safe filenames inside `app/uploads/`.
4. **Data Ownership & Backup**: Entire application state resides in `health_tracker.db` and `app/uploads/`. Backup is as simple as copying `health_tracker.db` to a USB stick.

---

## 8. Verification Plan & Test Results

### Automated Tests
- `test_backend.py`: Validates date parsing, biomarker dictionary mapping, status flags, and SQLite database operations.
- `test_pdf_upload.py`: End-to-end integration test parsing digital lab reports and asserting all REST endpoints.

### Running the App
```bash
# Windows 1-Click
.\run.bat

# Linux / macOS
chmod +x run.sh && ./run.sh
```
App URLs:
- Local browser: `http://localhost:8000`
- Phone/tablet on Wi-Fi: `http://<lan-ip>:8000` (displayed in the top banner)
