param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\RADAR-01"
$LatestBackupFile = Join-Path $Release ".latest-backup.txt"
$RuntimeSettings = Join-Path $Root "data\searxng\settings.yml"
$ComposeFile = Join-Path $Root "docker\compose.yml"

if (-not (Test-Path $LatestBackupFile)) {
    throw "No RADAR-01 backup reference exists."
}

$Backup = (Get-Content -LiteralPath $LatestBackupFile -Raw).Trim()
if (-not $Backup -or -not (Test-Path $Backup)) {
    throw "RADAR-01 backup folder was not found: $Backup"
}

$BackupSettings = Join-Path $Backup "settings.yml"
if (Test-Path $BackupSettings) {
    Copy-Item -Force $BackupSettings $RuntimeSettings
}
elseif (Test-Path (Join-Path $Backup "settings.yml.__missing__")) {
    Remove-Item -Force -ErrorAction SilentlyContinue $RuntimeSettings
}
else {
    throw "RADAR-01 backup entry is incomplete."
}

docker compose -f $ComposeFile up -d --force-recreate searxng
if ($LASTEXITCODE -ne 0) {
    throw "SearXNG could not be restarted after rollback."
}

Write-Host "RADAR-01 rollback PASSED."
Write-Host "Restored backup: $Backup"
