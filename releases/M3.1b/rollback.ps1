param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\M3.1b"
$LatestBackupFile = Join-Path $Release ".latest-backup.txt"
$ComposeFile = Join-Path $Root "docker\compose.yml"

$Targets = @(
    "backend\app\main.py",
    "backend\app\repositories\discovery_run_repository.py",
    "backend\app\routers\discovery_history.py",
    "backend\app\schemas\discovery_history.py"
)

if (-not (Test-Path $LatestBackupFile)) {
    throw "No M3.1b backup reference exists."
}

$Backup = (Get-Content $LatestBackupFile -Raw).Trim()

if (-not $Backup -or -not (Test-Path $Backup)) {
    throw "M3.1b backup folder not found: $Backup"
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

docker compose -f $ComposeFile restart backend

if ($LASTEXITCODE -ne 0) {
    throw "Backend restart failed after rollback."
}

Write-Host "M3.1b rollback PASSED."
Write-Host "Restored backup: $Backup"