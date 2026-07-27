param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\RADAR-03"
$LatestBackupFile = Join-Path $Release ".latest-backup.txt"
$TargetRelative = "frontend/src/pages/CampaignRadarPage.tsx"
$Target = Join-Path $Root $TargetRelative
$ComposeFile = Join-Path $Root "docker\compose.production.yml"
$EnvFile = Join-Path $Root "docker\.env.production.local"
$ComposeArgs = @(
    "--env-file", $EnvFile,
    "--project-name", "tmi-production",
    "-f", $ComposeFile
)

if (-not (Test-Path $LatestBackupFile)) {
    throw "No RADAR-03 backup reference exists."
}
$Backup = (Get-Content -LiteralPath $LatestBackupFile -Raw).Trim()
$Stored = Join-Path $Backup $TargetRelative
if (-not (Test-Path $Stored)) {
    throw "RADAR-03 backup file was not found."
}

Copy-Item -Force $Stored $Target
docker compose @ComposeArgs build frontend
if ($LASTEXITCODE -ne 0) {
    throw "Rollback frontend build failed."
}
docker compose @ComposeArgs up -d --no-deps --wait frontend
if ($LASTEXITCODE -ne 0) {
    throw "Rollback frontend deployment failed."
}

Write-Host "RADAR-03 rollback PASSED."
Write-Host "Restored backup: $Backup"
