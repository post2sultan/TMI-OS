param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\P2-01"
$LatestBackupFile = Join-Path $Release ".latest-backup.txt"
$Results = Join-Path $Release "results\evaluation.json"

if (-not (Test-Path $LatestBackupFile)) {
    throw "No P2-01 backup reference exists."
}
$Backup = (Get-Content -LiteralPath $LatestBackupFile -Raw).Trim()
if (Test-Path (Join-Path $Backup "evaluation.json")) {
    Copy-Item -Force (Join-Path $Backup "evaluation.json") $Results
}
elseif (Test-Path (Join-Path $Backup "evaluation.json.__missing__")) {
    Remove-Item -Force -ErrorAction SilentlyContinue $Results
}
else {
    throw "P2-01 backup is incomplete."
}

$ProductionModel = docker inspect tmi-production-backend-1 `
    --format '{{range .Config.Env}}{{println .}}{{end}}' |
    Where-Object { $_ -like "AI_PRIMARY_MODEL=*" } |
    Select-Object -First 1
if ($ProductionModel -ne "AI_PRIMARY_MODEL=qwen2.5:3b") {
    throw "Production model is not the pre-evaluation baseline."
}

Write-Host "P2-01 rollback PASSED."
Write-Host "Production model remains qwen2.5:3b."
