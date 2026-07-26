param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\GL-03"
$LatestBackupFile = Join-Path $Release ".latest-backup.txt"
$Targets = @(
    "frontend\.dockerignore",
    "frontend\.env.example",
    "frontend\Caddyfile",
    "frontend\Dockerfile",
    "frontend\src\lib\api.ts",
    "frontend\vite.config.ts",
    "docker\compose.production.yml",
    "docker\production.env.example",
    "scripts\validate-production-web.ps1",
    "docs\GO_LIVE.md"
)

if (-not (Test-Path $LatestBackupFile)) { throw "No GL-03 backup reference exists." }
$Backup = (Get-Content $LatestBackupFile -Raw).Trim()
if (-not $Backup -or -not (Test-Path $Backup)) {
    throw "GL-03 backup folder not found: $Backup"
}

foreach ($RelativePath in $Targets) {
    $Saved = Join-Path $Backup $RelativePath
    $Destination = Join-Path $Root $RelativePath
    if (Test-Path $Saved) {
        New-Item -ItemType Directory -Force (Split-Path -Parent $Destination) | Out-Null
        Copy-Item -Force $Saved $Destination
    }
    elseif (Test-Path "$Saved.__missing__") {
        Remove-Item -Force -ErrorAction SilentlyContinue $Destination
    }
    else {
        throw "Backup entry missing for: $RelativePath"
    }
}

$Health = Invoke-RestMethod "http://127.0.0.1:8000/health" -TimeoutSec 15
if ($Health.status -ne "healthy") { throw "Development backend is not healthy after rollback." }
Write-Host "GL-03 rollback PASSED."
Write-Host "Restored backup: $Backup"
