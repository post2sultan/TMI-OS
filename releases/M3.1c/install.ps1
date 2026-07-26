param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\M3.1c"
$Patch = Join-Path $Release "patch"
$BackupRoot = Join-Path $Release "backups"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Backup = Join-Path $BackupRoot $Timestamp
$LatestBackupFile = Join-Path $Release ".latest-backup.txt"
$Frontend = Join-Path $Root "frontend"
$BaseUrl = "http://127.0.0.1:8000"

$Targets = @(
    "frontend\src\lib\api.ts",
    "frontend\src\types\api.ts",
    "frontend\src\pages\CampaignRadarPage.tsx",
    "frontend\src\pages\AnalyticsPage.tsx",
    "frontend\src\pages\ApprovedPage.tsx",
    "frontend\src\pages\ReviewQueuePage.tsx"
)

function Restore-Backup {
    if (-not (Test-Path $Backup)) {
        return
    }

    foreach ($RelativePath in $Targets) {
        $BackupPath = Join-Path $Backup $RelativePath
        $TargetPath = Join-Path $Root $RelativePath
        $MissingMarker = "$BackupPath.__missing__"

        if (Test-Path $BackupPath) {
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $TargetPath) | Out-Null
            Copy-Item -Force $BackupPath $TargetPath
        }
        elseif (Test-Path $MissingMarker) {
            Remove-Item -Force -ErrorAction SilentlyContinue $TargetPath
        }
    }
}

try {
    if (-not (Test-Path (Join-Path $Frontend "package-lock.json"))) {
        throw "Frontend package lock was not found."
    }

    New-Item -ItemType Directory -Force -Path $Backup | Out-Null

    foreach ($RelativePath in $Targets) {
        $SourcePath = Join-Path $Patch $RelativePath
        $TargetPath = Join-Path $Root $RelativePath
        $BackupPath = Join-Path $Backup $RelativePath

        if (-not (Test-Path $SourcePath)) {
            throw "Patch file missing: $SourcePath"
        }

        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $BackupPath) | Out-Null

        if (Test-Path $TargetPath) {
            Copy-Item -Force $TargetPath $BackupPath
        }
        else {
            New-Item -ItemType File -Force -Path "$BackupPath.__missing__" | Out-Null
        }
    }

    Set-Content -Path $LatestBackupFile -Value $Backup -Encoding UTF8

    foreach ($RelativePath in $Targets) {
        $SourcePath = Join-Path $Patch $RelativePath
        $TargetPath = Join-Path $Root $RelativePath
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $TargetPath) | Out-Null
        Copy-Item -Force $SourcePath $TargetPath
    }

    Push-Location $Frontend
    try {
        & npm.cmd install --prefer-offline --no-audit --no-fund
        if ($LASTEXITCODE -ne 0) {
            throw "Frontend dependency installation failed."
        }

        & npm.cmd run build
        if ($LASTEXITCODE -ne 0) {
            throw "Frontend production build failed."
        }
    }
    finally {
        Pop-Location
    }

    $History = Invoke-RestMethod -Uri "$BaseUrl/discovery/history?limit=1&offset=0" -Method Get -TimeoutSec 15
    if ($History.limit -ne 1 -or $History.offset -ne 0) {
        throw "Live discovery-history API contract validation failed."
    }

    Write-Host ""
    Write-Host "M3.1c installation PASSED."
    Write-Host "Backup: $Backup"
}
catch {
    Write-Host ""
    Write-Host "M3.1c installation FAILED. Rolling back..." -ForegroundColor Red
    Restore-Backup
    throw
}
