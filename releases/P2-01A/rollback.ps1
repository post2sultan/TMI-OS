param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\P2-01A"
$LatestBackupFile = Join-Path $Release ".latest-backup.txt"
$Results = Join-Path $Release "results\evaluation.json"

if (-not (Test-Path $LatestBackupFile)) {
    throw "No P2-01A backup reference exists."
}
$Backup = (Get-Content -LiteralPath $LatestBackupFile -Raw).Trim()
if (Test-Path (Join-Path $Backup "evaluation.json")) {
    Copy-Item -Force (Join-Path $Backup "evaluation.json") $Results
}
elseif (Test-Path (Join-Path $Backup "evaluation.json.__missing__")) {
    Remove-Item -Force -ErrorAction SilentlyContinue $Results
}
else {
    throw "P2-01A backup is incomplete."
}

Write-Host "P2-01A rollback PASSED."
Write-Host "Production was not changed by this evaluation."
