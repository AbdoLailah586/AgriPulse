@echo off
chcp 65001 > nul
title AgriPulse Frontend Runner

echo ==================================================================
echo   🌱 AgriPulse - نظام التشغيل الذكي للمضخات وشبكات الري الزراعي
echo   🚀 تشغيل واجهة المستخدم التفاعلية (Frontend)
echo ==================================================================

cd /d "%~dp0\..\frontend"

where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH.
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)

if not exist ".env" (
    if exist ".env.example" (
        copy /y ".env.example" ".env" > nul
        echo [INFO] Created .env from .env.example
    )
)

if not exist "node_modules" (
    echo [INFO] Installing frontend packages...
    call npm install
    if %errorlevel% neq 0 (
        echo [ERROR] npm install failed.
        pause
        exit /b 1
    )
)

echo [INFO] Starting browser at http://localhost:5173 ...
start "" "http://localhost:5173"

echo [INFO] Launching Vite development server...
call npm run dev
pause
