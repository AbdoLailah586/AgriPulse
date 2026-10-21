@echo off
setlocal
cd /d "%~dp0\.."

set REPO_URL=https://github.com/AbdoLailah586/AgriPulse.git
set BRANCH=Abdo

if not "%~1"=="" set BRANCH=%~1

echo ==========================================================
echo  AgriPulse - Pull from GitHub (Branch: %BRANCH%)
echo ==========================================================

git remote | findstr /R "^origin$" >nul
if %errorlevel% neq 0 (
    echo [INFO] Adding remote origin...
    git remote add origin %REPO_URL%
) else (
    git remote set-url origin %REPO_URL%
)

echo [INFO] Fetching latest changes...
git fetch origin

git checkout %BRANCH% 2>nul || git checkout -b %BRANCH% origin/%BRANCH%

echo [INFO] Pulling from %REPO_URL% (%BRANCH%)...
git pull origin %BRANCH%

if %errorlevel% equ 0 (
    echo ==========================================================
    echo  [SUCCESS] Pulled latest updates successfully!
    echo ==========================================================
) else (
    echo ==========================================================
    echo  [ERROR] Pull failed. Check git status or conflicts.
    echo ==========================================================
)
pause
