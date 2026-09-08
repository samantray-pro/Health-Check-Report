#!/usr/bin/env bash
echo "======================================================="
echo "    HEALTH CHECKUP TRACKER - LOCAL PRIVACY EDITION"
echo "======================================================="
echo ""

if [ ! -d ".venv" ]; then
    echo "[1/3] Creating virtual environment..."
    python3 -m venv .venv
fi

echo "[2/3] Checking dependencies..."
./.venv/bin/pip install -r requirements.txt --quiet

echo ""
echo "[3/3] Starting Local Health Checkup Tracker..."
echo "Open in browser: http://localhost:8000"
echo ""

./.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
