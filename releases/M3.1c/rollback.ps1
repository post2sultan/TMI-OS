param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\M3.1c"
$LatestBackupFile = Join-Path $Release ".latest-backup.txt"
$Frontend = Join-Path $Root "frontend"

$Targets = @(
    "frontend\src\lib\api.ts",
    "frontend\src\types\api.ts",
    "frontend\src\pages\CampaignRadarPage.tsx",
    "frontend\src\pages\AnalyticsPage.tsx",
    "frontend\src\pages\ApprovedPage.tsx",
    "frontend\src\pages\ReviewQueuePage.tsx"
)

if (-not (Test-Path $LatestBackupFile)) {
    throw "No M3.1c backup reference exists."
}

$Backup = (Get-Content $LatestBackupFile -Raw).Trim()
if (-not $Backup -or -not (Test-Path $Backup)) {
    throw "M3.1c backup folder not found: $Backup"
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
    else {
        throw "Backup entry missing for: $RelativePath"
    }
}

Push-Location $Frontend
try {
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend build failed after rollback."
    }
}
finally {
    Pop-Location
}

Write-Host "M3.1c rollback PASSED."
Write-Host "Restored backup: $Backup"
