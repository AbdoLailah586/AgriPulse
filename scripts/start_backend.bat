@echo off
chcp 65001 > nul
title AgriPulse Unified API Gateway (Port 8000)

echo ==================================================================
echo   🌱 AgriPulse - نظام التشغيل الذكي للمضخات وشبكات الري الزراعي
echo   🚀 تشغيل الخادم الموحد وبوابة الواجهات (Unified API Gateway: 8000)
echo ==================================================================

cd /d "%~dp0\.."

set "PYTHON_EXE=.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=python"
)

echo [INFO] Using Python interpreter: %PYTHON_EXE%
echo [INFO] Starting FastAPI Unified Gateway on http://localhost:8000 ...
echo [INFO] Interactive API Docs available at http://localhost:8000/docs
echo [INFO] Press Ctrl+C to stop the server.
echo.

"%PYTHON_EXE%" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

pause
