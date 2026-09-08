# 🩺 Health Checkup Tracker (Local, Private & AI-Powered)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Database](https://img.shields.io/badge/SQLite3-Raw%20Driver%20(No%20ORM)-003B57.svg?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Frontend](https://img.shields.io/badge/Frontend-Vanilla%20HTML%20%7C%20CSS%20%7C%20JS-F7DF1E.svg?logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![Privacy](https://img.shields.io/badge/Privacy-100%25%20Offline%20%26%20Local-success.svg)](https://github.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight, modern, and privacy-first longitudinal health analytics web application for digitizing, comparing, and tracking medical checkups across family members. 

Equipped with an automated PDF/OCR biomarker ingestion engine and an integrated **Dual-Provider AI Assistant** (supporting both **100% Offline Ollama** and **Google Gemini Cloud AI**), Health Checkup Tracker transforms scattered paper reports into actionable health insights over months and years.

---

## 📑 Table of Contents

- [Vision & Core Capabilities](#-vision--core-capabilities)
- [System Architecture](#-system-architecture)
- [Prerequisites](#-prerequisites)
- [How to Execute the Web App](#-how-to-execute-the-web-app)
  - [Option 1: Automated Script (Recommended)](#option-1-automated-script-recommended)
  - [Option 2: Manual Terminal Execution](#option-2-manual-terminal-execution)
- [AI Health Assistant Setup](#-ai-health-assistant-setup)
  - [🦙 Local Offline AI (Ollama Guide)](#-option-a-local-offline-ai-ollama)
  - [⚡ Google Gemini Cloud AI (Gemini Guide)](#-option-b-google-gemini-cloud-ai)
  - [Provider Comparison](#provider-comparison)
- [Accessing from Mobile / LAN Devices](#-accessing-from-mobile--lan-devices)
- [Supported Biomarkers & Lab Formats](#-supported-biomarkers--lab-formats)
- [Repository Structure](#-repository-structure)
- [Data Privacy & Backup Protocols](#-data-privacy--backup-protocols)
- [Troubleshooting & FAQs](#-troubleshooting--faqs)
- [Medical Disclaimer](#-medical-disclaimer)

---

## 🎯 Vision & Core Capabilities

1. **Centralized Multi-Persona Tracking**: Create and toggle instantly between profiles for different family members (e.g. *Self*, *Mother*, *Father*, *Spouse*) with zero login friction.
2. **Automated Report Extraction (PDF & OCR)**: Upload digital PDF lab reports from any major diagnostic provider (Apollo Diagnostics, Tata 1mg, Dr. Lal PathLabs, Metropolis, SRL Diagnostics, etc.). The system automatically extracts test names, values, units, biological reference intervals, and flags out-of-range biomarkers.
3. **Longitudinal Biomarker Comparison**: See how biomarkers (e.g., HbA1c, Fasting Blood Sugar, LDL Cholesterol, Vitamin D, TSH) evolve over consecutive checkups with embedded sparklines and interactive trend modal charts.
4. **Intelligent AI Health Assistant**: Ask questions about your lab results in plain English (*"How has my lipid profile changed over the last two years?"* or *"What do my flagged liver enzymes mean?"*). The assistant streams contextualized, clinical explanations with real-time thinking micro-animations.
5. **100% Privacy & Offline-First**: No telemetry, no external accounts, no cloud sync. Everything stays on your local machine.

---

## 🏗️ System Architecture

The application is engineered to be blazing fast, dependency-minimal, and completely free of build tooling:

```
┌───────────────────────────────────────────────────────────┐
│                    User Browser Interface                 │
│  Vanilla HTML5 · Clinical CSS Design Tokens · Vanilla JS  │
│  (No Webpack, No Vite, No Tailwind, No Build Step Needed) │
└──────────────┬─────────────────────────────▲──────────────┘
               │ HTTP / SSE Stream           │ Dynamic DOM Updates
┌──────────────▼─────────────────────────────┴──────────────┐
│                    FastAPI Backend Router                 │
│  Async Endpoints · StreamingResponse · Error Interceptors │
└──────┬──────────────────┬──────────────────┬──────────────┘
       │                  │                  │
┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────────────┐
│   SQLite3   │    │ PDF Extract │    │  AI Inference Hub   │
│ Raw Driver  │    │ pdfplumber  │    │ ┌─────────────────┐ │
│  (No ORMs)  │    │ +Tesseract  │    │ │ Ollama (Local)  │ │
│ health_     │    │ OCR Engine  │    │ ├─────────────────┤ │
│ tracker.db  │    │             │    │ │ Gemini (Cloud)  │ │
└─────────────┘    └─────────────┘    │ └─────────────────┘ │
                                      └─────────────────────┘
```

* **Persistence Layer**: Strictly raw `sqlite3` using `sqlite3.Row` and the `get_db()` context manager. **Zero ORMs** (no SQLAlchemy or Peewee overhead) for instantaneous query execution.
* **Frontend Layer**: Vanilla HTML5, modern CSS custom properties (`style.css`), and lightweight ES6+ JavaScript (`app.js`). Chart.js is loaded for medical trend visualization.
* **Extraction Engine**: Hybrid extraction pipeline utilizing `pdfplumber` for vector text parsing and `pytesseract` for image-based OCR scans.
* **Streaming AI Protocol**: Server-Sent Events (`text/event-stream`) delivering token-by-token generation with an immediate handshake.

---

## 📋 Prerequisites

Before running the application, make sure you have the following installed:

### 1. Python Environment
* **Python 3.10** or higher is required.
* Verify your installation:
  ```bash
  python --version
  ```

### 2. Optional: Tesseract OCR (For Scanned Paper Images)
* **Digital PDF reports** (downloaded from lab portals) work out of the box with zero external dependencies.
* **Scanned physical paper photos** require Tesseract OCR:
  * **Windows**: Download the installer from [UB-Mannheim Tesseract Wiki](https://github.com/UB-Mannheim/tesseract/wiki) and add it to your system PATH.
  * **macOS**: `brew install tesseract`
  * **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`

### 3. Optional: AI Provider Prerequisites
* To use **Local Offline AI**: Install [Ollama](https://ollama.com/) (see the [Local AI Setup Guide](docs/LOCAL_AI_SETUP.md)).
* To use **Gemini Cloud AI**: An internet connection and a free API Key from [Google AI Studio](https://aistudio.google.com/app/apikey) (see the [Gemini Setup Guide](docs/GEMINI_SETUP.md)).

---

## 🚀 How to Execute the Web App

### Option 1: Automated Script (Recommended)

#### On Windows:
Double-click `run.bat` or execute in PowerShell:
```powershell
.\run.bat
```
*What this script does:*
1. Automatically detects or creates the isolated `.venv` virtual environment.
2. Installs required packages from `requirements.txt`.
3. Launches the local Uvicorn server at `http://0.0.0.0:8000` with auto-reload.

#### On Linux / macOS:
```bash
chmod +x run.sh
./run.sh
```

---

### Option 2: Manual Terminal Execution

If you prefer to configure and run the environment manually:

1. **Clone or Navigate to the Repository**:
   ```bash
   cd "c:\Codes\Health Check Report"
   ```

2. **Create and Activate a Virtual Environment**:
   * **Windows (PowerShell)**:
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   * **Linux / macOS**:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the Web Application**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **Open in Your Browser**:
   Visit [http://localhost:8000](http://localhost:8000) in any modern browser.

---

## 🤖 AI Health Assistant Setup

The Health Checkup Tracker features an intelligent AI Chatbot accessible via the floating 💬 button at the bottom-right of the dashboard. It dynamically summarizes historical biomarkers, highlights out-of-range findings, and explains medical terms.

You can toggle between two AI engines in the **"🤖 AI Config"** settings modal:

```
┌───────────────────────────────────────────────────────────┐
│              Choose Your AI Provider                      │
├─────────────────────────────┬─────────────────────────────┤
│   🦙 Local Offline (Ollama) │   ⚡ Google Gemini (Cloud)   │
│   100% Private, zero cloud  │   Instant responses, no     │
│   data transfer. Runs on    │   hardware requirements.    │
│   your CPU/GPU/NPU.         │   Free tier available.      │
│                             │                             │
│   👉 [Read Local AI Guide]  │   👉 [Read Gemini Guide]    │
│      (docs/LOCAL_AI_SETUP)  │      (docs/GEMINI_SETUP)    │
└─────────────────────────────┴─────────────────────────────┘
```

### 🦙 Option A: Local Offline AI (Ollama)
* Best for **maximum medical privacy**. Your lab numbers and health trends never leave your machine.
* Compatible with models like `phi3:3.8b`, `llama3.2:3b`, and `gemma2:2b`.
* Includes automatic memory clamping (`num_ctx: 2048`) to avoid Out-Of-Memory crashes on laptop hardware.
* 👉 **Follow the complete step-by-step tutorial**: [**Local AI Setup Guide (Ollama)**](docs/LOCAL_AI_SETUP.md)

### ⚡ Option B: Google Gemini Cloud AI
* Best for **high-speed performance** without burdening your computer's CPU or battery.
* Utilizes Google's production models: **`gemini-3.5-flash`** and **`gemini-3.5-flash-lite`**.
* Features pre-emptive deprecation remapping and an automated fallback cascade so you never hit 404 errors.
* Your API key is saved **only in your browser's local storage**.
* 👉 **Follow the complete step-by-step tutorial**: [**Google Gemini Setup Guide**](docs/GEMINI_SETUP.md)

---

### Provider Comparison

| Feature | 🦙 Local Offline (Ollama) | ⚡ Google Gemini (Cloud) |
| :--- | :--- | :--- |
| **Privacy** | **100% Local** (Zero external network calls) | Sent ephemerally via Google API |
| **Hardware Needed** | 8 GB+ RAM, modern multi-core CPU/GPU | Any device (works on low-end laptops & phones) |
| **Latency** | 3 - 8s prompt ingestion on CPU | < 400ms instant streaming |
| **Setup Effort** | Install Ollama + download model (~2GB) | Paste free API Key from Google AI Studio |
| **Offline Support**| Fully functional without Internet | Requires active Internet connection |
| **Detailed Setup** | [**Ollama Setup Guide**](docs/LOCAL_AI_SETUP.md) | [**Gemini Setup Guide**](docs/GEMINI_SETUP.md) |

---

## 📱 Accessing from Mobile / LAN Devices

The Health Checkup Tracker binds to `0.0.0.0:8000`, making it immediately accessible to smartphones, tablets, and other PCs on your local Wi-Fi network.

1. Ensure your computer and phone are connected to the **same Wi-Fi network**.
2. Look at the **Local Network Banner** at the top of the desktop browser window (e.g., `http://192.168.1.15:8000`).
3. Open that address in your mobile browser (Safari, Chrome, Firefox).
4. You can take photos of reports with your phone camera, upload PDFs, and chat with the AI assistant seamlessly on mobile!

> [!TIP]
> If your phone cannot connect, verify that your computer's firewall allows incoming connections on port `8000`.

---

## 🧪 Supported Biomarkers & Lab Formats

The ingestion engine parses and aggregates biomarkers across all standard diagnostic panels:

* **Complete Blood Count (CBC)**: Hemoglobin, RBC, WBC, Platelet Count, Hematocrit/PCV, MCV, MCH, MCHC, Neutrophils, Lymphocytes, Eosinophils, Monocytes, Basophils.
* **Diabetic Profile**: HbA1c, Estimated Average Glucose (eAG), Fasting Blood Glucose, Post-Prandial Blood Glucose.
* **Lipid Profile**: Total Cholesterol, Triglycerides, HDL ("Good") Cholesterol, LDL ("Bad") Cholesterol, VLDL, Non-HDL Cholesterol, TC/HDL Ratio.
* **Liver Function Test (LFT)**: SGOT (AST), SGPT (ALT), Alkaline Phosphatase (ALP), Total Bilirubin, Direct Bilirubin, Total Protein, Albumin, Globulin, A/G Ratio.
* **Kidney Function Test (KFT / RFT)**: Blood Urea, Serum Creatinine, Uric Acid, BUN, eGFR, Calcium, Phosphorus.
* **Thyroid Profile**: T3, T4, TSH (Thyroid Stimulating Hormone).
* **Vitamins & Micronutrients**: Vitamin D (25-Hydroxy), Vitamin B12, Serum Iron, Ferritin, Total Iron Binding Capacity (TIBC).

---

## 📂 Repository Structure

```
Health Check Report/
├── .agents/
│   └── AGENTS.md                  # Architectural rules, memory & system guidelines
├── app/
│   ├── ai_router.py               # AI dual-engine router (Ollama + Gemini streaming SSE)
│   ├── database.py                # Raw SQLite connection manager & table bootstrap
│   ├── main.py                    # FastAPI application initialization & static routes
│   ├── ocr_engine.py              # Hybrid PDF text parsing & Tesseract OCR pipeline
│   ├── parsers.py                 # Clinical regex patterns & reference range extractors
│   └── routes.py                  # REST API for profiles, test records & trend lookups
├── docs/
│   ├── GEMINI_SETUP.md            # Step-by-step setup guide for Google Gemini Cloud AI
│   └── LOCAL_AI_SETUP.md          # Step-by-step setup guide for Ollama Local Offline AI
├── static/
│   ├── css/
│   │   └── style.css              # Dark clinical design system, animations & tokens
│   ├── js/
│   │   └── app.js                 # Vanilla frontend state, charts, chat & SSE decoder
│   └── index.html                 # Main dashboard UI, modals & chat interface
├── health_tracker.db              # Local SQLite database file (created on first run)
├── requirements.txt               # Python package dependencies
├── run.bat                        # Windows 1-click startup batch script
├── run.sh                         # Linux / macOS 1-click startup shell script
└── README.md                      # Primary project documentation
```

---

## 🔒 Data Privacy & Backup Protocols

* **Zero Cloud Storage**: All patient demographics, test dates, and clinical measurements reside exclusively in `health_tracker.db` inside your project folder.
* **No Telemetry**: No third-party trackers, cookies, or analytics scripts are loaded.
* **Effortless Backups**: Because all state is stored in a single SQLite file, creating a backup is as simple as copying `health_tracker.db` to a secure USB drive or encrypted storage.
* **To Reset / Clear All Data**: Simply delete `health_tracker.db`. The application will initialize a fresh, clean database upon the next start.

---

## ❓ Troubleshooting & FAQs

<details>
<summary><strong>1. The port 8000 is already in use. How do I change it?</strong></summary>

Edit line 26 in `run.bat` (or line 14 in `run.sh`) and change `--port 8000` to an open port (e.g. `--port 8080`):
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```
</details>

<details>
<summary><strong>2. Why are my uploaded scanned PDF reports taking a while to process?</strong></summary>

Vector-based digital PDFs process in milliseconds. If your PDF is a scanned image or photograph of a physical paper, the application automatically invokes Tesseract OCR, which may take 5 to 15 seconds per page depending on your CPU speed.
</details>

<details>
<summary><strong>3. The chat widget shows an error when asking questions. What should I check?</strong></summary>

* **If using Local AI**: Ensure Ollama is running (`ollama list`) and accessible at `http://localhost:11434`. Review the [Local AI Setup Guide](docs/LOCAL_AI_SETUP.md).
* **If using Gemini**: Ensure your API key is valid and you have selected an active model (such as `gemini-3.5-flash`). Review the [Gemini Setup Guide](docs/GEMINI_SETUP.md).
* **Browser Cache**: Press `Ctrl + F5` to force-reload the latest JavaScript and CSS.
</details>

---

## ⚖️ Medical Disclaimer

Health Checkup Tracker is a personal data management and educational visualization tool. It is **not a certified medical device** and does not provide formal medical diagnoses, clinical treatment plans, or emergency recommendations. 

Always consult a qualified healthcare professional or your physician to interpret abnormal biomarker findings or adjust prescription medications.

---

## 📜 License

This project is open-source software licensed under the [MIT License](LICENSE).
