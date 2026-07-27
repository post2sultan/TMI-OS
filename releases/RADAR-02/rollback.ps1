param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\RADAR-02"
$LatestBackupFile = Join-Path $Release ".latest-backup.txt"
$ComposeFile = Join-Path $Root "docker\compose.yml"
$Targets = @(
    "backend/app/services/discovery/manager.py",
    "backend/tests/test_discovery_google_news_links.py"
)

if (-not (Test-Path $LatestBackupFile)) {
    throw "No RADAR-02 backup reference exists."
}
$Backup = (Get-Content -LiteralPath $LatestBackupFile -Raw).Trim()
if (-not $Backup -or -not (Test-Path $Backup)) {
    throw "RADAR-02 backup folder was not found: $Backup"
}

foreach ($RelativePath in $Targets) {
    $Target = Join-Path $Root $RelativePath
    $Stored = Join-Path $Backup $RelativePath
    if (Test-Path $Stored) {
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Target) | Out-Null
        Copy-Item -Force $Stored $Target
    }
    elseif (Test-Path "$Stored.__missing__") {
        Remove-Item -Force -ErrorAction SilentlyContinue $Target
    }
    else {
        throw "RADAR-02 backup entry is incomplete: $RelativePath"
    }
}

docker compose -f $ComposeFile restart backend
if ($LASTEXITCODE -ne 0) {
    throw "Backend restart failed after rollback."
}

Write-Host "RADAR-02 rollback PASSED."
Write-Host "Restored backup: $Backup"
