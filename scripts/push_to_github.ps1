<#
.SYNOPSIS
    Pushes project changes to GitHub on branch 'Abdo'.

.DESCRIPTION
    Configures remote 'origin' to https://github.com/AbdoLailah586/AgriPulse.git,
    creates or switches to branch 'Abdo', stages tracked & new files, commits, and pushes upstream.

.PARAMETER CommitMessage
    Custom commit message. Defaults to a descriptive feature update message.

.PARAMETER Branch
    Target Git branch. Defaults to 'Abdo'.
#>

param(
    [string]$CommitMessage = "feat: update project documentation flow, architecture blueprints, and sync automation",
    [string]$Branch = "Abdo"
)

$ErrorActionPreference = "Stop"
$RepoUrl = "https://github.com/AbdoLailah586/AgriPulse.git"

# Navigate to project root (parent directory of scripts/)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " AgriPulse - Push to GitHub (Branch: $Branch)" -ForegroundColor Cyan
Write-Host " Working Directory: $ProjectRoot" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Verify Git is initialized
if (-not (Test-Path ".git")) {
    Write-Host "[ERROR] Git repository not found. Initializing git..." -ForegroundColor Yellow
    git init
}

# 2. Configure Remote URL
$Remotes = git remote
if ($Remotes -contains "origin") {
    $CurrentRemote = (git remote get-url origin).Trim()
    if ($CurrentRemote -ne $RepoUrl) {
        Write-Host "[INFO] Updating remote 'origin' to $RepoUrl..." -ForegroundColor Yellow
        git remote set-url origin $RepoUrl
    } else {
        Write-Host "[OK] Remote 'origin' is already set to $RepoUrl" -ForegroundColor Green
    }
} else {
    Write-Host "[INFO] Adding remote 'origin' -> $RepoUrl..." -ForegroundColor Yellow
    git remote add origin $RepoUrl
}

# 3. Check out or create target branch
$CurrentBranch = (git branch --show-current).Trim()
if ($CurrentBranch -ne $Branch) {
    # Check if branch exists locally
    $LocalBranches = (git branch --list $Branch)
    if ($LocalBranches) {
        Write-Host "[INFO] Switching to existing local branch '$Branch'..." -ForegroundColor Cyan
        git checkout $Branch
    } else {
        Write-Host "[INFO] Creating and switching to new branch '$Branch'..." -ForegroundColor Cyan
        git checkout -b $Branch
    }
} else {
    Write-Host "[OK] Already on branch '$Branch'." -ForegroundColor Green
}

# 4. Stage changes
Write-Host "[INFO] Staging files..." -ForegroundColor Cyan
git add .

# 5. Commit changes if any exist
$GitStatus = (git status --porcelain)
if ($GitStatus) {
    Write-Host "[INFO] Committing changes with message: '$CommitMessage'..." -ForegroundColor Cyan
    git commit -m $CommitMessage
} else {
    Write-Host "[INFO] No unstaged/uncommitted changes detected. Proceeding to push..." -ForegroundColor Yellow
}

# 6. Push to remote
Write-Host "[INFO] Pushing branch '$Branch' to origin ($RepoUrl)..." -ForegroundColor Cyan
try {
    git push -u origin $Branch
    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host " [SUCCESS] Project successfully pushed to GitHub on branch '$Branch'!" -ForegroundColor Green
    Write-Host " URL: https://github.com/AbdoLailah586/AgriPulse/tree/$Branch" -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Red
    Write-Host " [ERROR] Failed to push to GitHub. Details:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host " If authentication is required, make sure your GitHub credentials / token are configured." -ForegroundColor Yellow
    Write-Host "==========================================================" -ForegroundColor Red
    exit 1
}
