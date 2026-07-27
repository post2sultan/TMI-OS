param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\P2-01"
$Results = Join-Path $Release "results\evaluation.json"
$Backup = Join-Path $Release "backups\$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$LatestBackupFile = Join-Path $Release ".latest-backup.txt"
$EnvFile = Join-Path $Root "docker\.env.production.local"
$ComposeFile = Join-Path $Root "docker\compose.production.yml"

New-Item -ItemType Directory -Force -Path $Backup | Out-Null
if (Test-Path $Results) {
    Copy-Item -Force $Results (Join-Path $Backup "evaluation.json")
}
else {
    New-Item -ItemType File -Path (Join-Path $Backup "evaluation.json.__missing__") | Out-Null
}
Set-Content -LiteralPath $LatestBackupFile -Value $Backup -Encoding utf8

$Models = docker exec tmi-production-ollama-1 ollama list
if (($Models | Out-String) -notmatch "qwen2.5:3b") {
    throw "Baseline model qwen2.5:3b is unavailable."
}
if (($Models | Out-String) -notmatch "qwen2.5:7b") {
    throw "Candidate model qwen2.5:7b is unavailable."
}

docker compose --env-file $EnvFile --project-name tmi-production `
    -f $ComposeFile run --rm --no-deps `
    -v "$($Release):/evaluation" `
    -e "PYTHONPATH=/app" `
    backend python -B /evaluation/evaluate.py `
    /evaluation/results/evaluation.json
if ($LASTEXITCODE -ne 0) {
    throw "P2-01 bounded model evaluation failed."
}

& (Join-Path $Release "validate.ps1") -Root $Root

Write-Host ""
Write-Host "P2-01 installation PASSED."
Write-Host "Results: $Results"
