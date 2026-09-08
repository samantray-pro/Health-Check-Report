@echo off
title Health Checkup Tracker (Local & Private)
echo =======================================================
echo     HEALTH CHECKUP TRACKER - LOCAL PRIVACY EDITION
echo =======================================================
echo.

IF NOT EXIST ".venv" (
    echo [1/3] Creating virtual environment...
    python -m venv .venv
)

echo [2/3] Checking dependencies...
call .\.venv\Scripts\pip.exe install -r requirements.txt --quiet

echo.
echo [3/3] Starting Local Health Checkup Tracker...
echo.
echo -------------------------------------------------------
echo  App is starting!
echo  Open in your browser: http://localhost:8000
echo  Or from your phone: Check the banner at top of the page
echo -------------------------------------------------------
echo.

call .\.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --reload
pause
