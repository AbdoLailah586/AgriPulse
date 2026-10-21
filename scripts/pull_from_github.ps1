<#
.SYNOPSIS
    Pulls latest project changes from GitHub.

.DESCRIPTION
    Ensures remote 'origin' is set to https://github.com/AbdoLailah586/AgriPulse.git,
    fetches latest commits, and pulls updates from GitHub into the active or specified branch.

.PARAMETER Branch
    Branch to pull from. Defaults to 'Abdo'.
#>

param(
    [string]$Branch = "Abdo"
)

$ErrorActionPreference = "Stop"
$RepoUrl = "https://github.com/AbdoLailah586/AgriPulse.git"

# Navigate to project root (parent directory of scripts/)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " AgriPulse — Pull from GitHub (Branch: $Branch)" -ForegroundColor Cyan
Write-Host " Working Directory: $ProjectRoot" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Verify Git is initialized
if (-not (Test-Path ".git")) {
    Write-Host "[ERROR] Git repository not found!" -ForegroundColor Red
    exit 1
}

# 2. Configure Remote URL if needed
$Remotes = git remote
if ($Remotes -contains "origin") {
    $CurrentRemote = (git remote get-url origin).Trim()
    if ($CurrentRemote -ne $RepoUrl) {
        Write-Host "[INFO] Updating remote 'origin' to $RepoUrl..." -ForegroundColor Yellow
        git remote set-url origin $RepoUrl
    }
} else {
    Write-Host "[INFO] Adding remote 'origin' -> $RepoUrl..." -ForegroundColor Yellow
    git remote add origin $RepoUrl
}

# 3. Fetch from remote
Write-Host "[INFO] Fetching latest branches and tags from origin..." -ForegroundColor Cyan
git fetch origin

# 4. Check out target branch if needed
$CurrentBranch = (git branch --show-current).Trim()
if ($CurrentBranch -ne $Branch) {
    Write-Host "[INFO] Switching from '$CurrentBranch' to '$Branch'..." -ForegroundColor Cyan
    git checkout $Branch
}

# 5. Pull changes
Write-Host "[INFO] Pulling latest changes from origin/$Branch..." -ForegroundColor Cyan
try {
    git pull origin $Branch
    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host " [SUCCESS] Repository updated to latest commits on '$Branch'!" -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Red
    Write-Host " [ERROR] Pull failed. Details:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host " If there are merge conflicts, review 'git status' and resolve them." -ForegroundColor Yellow
    Write-Host "==========================================================" -ForegroundColor Red
    exit 1
}
