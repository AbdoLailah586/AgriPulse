<#
.SYNOPSIS
    AgriPulse Frontend Runner - Smart Irrigation & Autonomous Pump Telemetry
.DESCRIPTION
    Automates environment verification, dependency installation, and starts the Vite development server.
    Automatically launches the application in the default web browser.
#>

$ErrorActionPreference = "Stop"

# Set encoding for Arabic and Unicode characters
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "  🌱 AgriPulse - نظام التشغيل الذكي للمضخات وشبكات الري الزراعي" -ForegroundColor Green
Write-Host "  🚀 جاري تجهيز وتشغيل الواجهة الأمامية (Frontend Development Server)" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan

# 1. Locate directories
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$FrontendDir = Join-Path $ProjectRoot "frontend"

if (-not (Test-Path $FrontendDir)) {
    Write-Host "[X] خطأ: مجلد frontend غير موجود في $FrontendDir" -ForegroundColor Red
    exit 1
}

# 2. Check Node.js and npm
Write-Host "`n[1/4] فحص بيئة Node.js و npm..." -ForegroundColor Yellow
try {
    $nodeVersion = & node -v
    $npmVersion = & npm -v
    Write-Host "  ✓ تم العثور على Node.js: $nodeVersion" -ForegroundColor Green
    Write-Host "  ✓ تم العثور على npm: v$npmVersion" -ForegroundColor Green
} catch {
    Write-Host "[X] خطأ: Node.js أو npm غير مثبت على جهازك." -ForegroundColor Red
    Write-Host "يرجى تثبيت Node.js من: https://nodejs.org" -ForegroundColor Yellow
    exit 1
}

# 3. Check environment file (.env)
Set-Location $FrontendDir
Write-Host "`n[2/4] فحص ملف الإعدادات (.env)..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "  ✓ تم إنشاء ملف .env تلقائياً من .env.example (وضع المحاكاة المستقل VITE_USE_MOCK_DATA=true)" -ForegroundColor Green
    } else {
        Set-Content -Path ".env" -Value "VITE_USE_MOCK_DATA=true`nVITE_API_BASE_URL=http://localhost:8000/api`nVITE_ENV=development"
        Write-Host "  ✓ تم إنشاء ملف .env افتراضي" -ForegroundColor Green
    }
} else {
    Write-Host "  ✓ ملف .env موجود وجاهز" -ForegroundColor Green
}

# 4. Check dependencies (node_modules)
Write-Host "`n[3/4] فحص حزم ومكتبات المشروع (node_modules)..." -ForegroundColor Yellow
if (-not (Test-Path "node_modules")) {
    Write-Host "  -> الحزم غير مثبتة، جاري تشغيل npm install الآن (يرجى الانتظار دقيقة)..." -ForegroundColor Cyan
    & npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[X] حدث خطأ أثناء تثبيت الحزم." -ForegroundColor Red
        exit 1
    }
    Write-Host "  ✓ تم تثبيت جميع الحزم بنجاح!" -ForegroundColor Green
} else {
    Write-Host "  ✓ الحزم مثبتة وجاهزة للتشغيل." -ForegroundColor Green
}

# 5. Start dev server and open browser
Write-Host "`n[4/4] بدء تشغيل السيرفر وفتح المتصفح..." -ForegroundColor Yellow
Write-Host "------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host "  🌐 الرابط المحلي: http://localhost:5173" -ForegroundColor Green
Write-Host "  🔑 الدخول التجريبي: اضغط على زر '1-Tap Demo: Lead Engineer' في صفحة الدخول" -ForegroundColor Yellow
Write-Host "     أو استخدم الحساب: tariq@agripulse.ai" -ForegroundColor Yellow
Write-Host "  ⏹️ لإيقاف السيرفر: اضغط Ctrl + C في نافذة الأوامر" -ForegroundColor DarkGray
Write-Host "------------------------------------------------------------------" -ForegroundColor DarkGray

# Open browser asynchronously after 1.5 seconds
Start-Job -ScriptBlock {
    Start-Sleep -Milliseconds 1500
    Start-Process "http://localhost:5173"
} | Out-Null

# Run Vite dev server
& npm run dev
