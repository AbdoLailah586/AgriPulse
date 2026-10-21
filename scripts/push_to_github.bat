@echo off
setlocal
cd /d "%~dp0\.."

set REPO_URL=https://github.com/AbdoLailah586/AgriPulse.git
set BRANCH=Abdo
set COMMIT_MSG=feat: update project documentation flow, architecture blueprints, and sync automation

if not "%~1"=="" set COMMIT_MSG=%~1

echo ==========================================================
echo  AgriPulse - Push to GitHub (Branch: %BRANCH%)
echo ==========================================================

git remote | findstr /R "^origin$" >nul
if %errorlevel% neq 0 (
    echo [INFO] Adding remote origin...
    git remote add origin %REPO_URL%
) else (
    git remote set-url origin %REPO_URL%
)

git checkout %BRANCH% 2>nul || git checkout -b %BRANCH%
git add .
git status --porcelain | findstr /R "." >nul
if %errorlevel% equ 0 (
    echo [INFO] Committing changes...
    git commit -m "%COMMIT_MSG%"
)

echo [INFO] Pushing to %REPO_URL% (%BRANCH%)...
git push -u origin %BRANCH%

if %errorlevel% equ 0 (
    echo ==========================================================
    echo  [SUCCESS] Pushed successfully to branch %BRANCH%!
    echo ==========================================================
) else (
    echo ==========================================================
    echo  [ERROR] Push failed. Check your internet connection or git credentials.
    echo ==========================================================
)
pause
