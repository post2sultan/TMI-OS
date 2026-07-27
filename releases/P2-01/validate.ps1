param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Results = Join-Path $Root "releases\P2-01\results\evaluation.json"
if (-not (Test-Path $Results)) {
    throw "P2-01 evaluation results are missing."
}
$Data = Get-Content -LiteralPath $Results -Raw | ConvertFrom-Json

if ($Data.total_runs -ne 4 -or $Data.runs_per_model -ne 2) {
    throw "P2-01 run ceiling or repetition count is invalid."
}
if ($Data.paid_api_credits -ne 0) {
    throw "P2-01 unexpectedly consumed paid API credits."
}
if ($Data.production_model_changed) {
    throw "P2-01 changed the production model unexpectedly."
}
if ($Data.models.Count -ne 2) {
    throw "P2-01 evaluated an unexpected model count."
}

$ProductionModel = docker inspect tmi-production-backend-1 `
    --format '{{range .Config.Env}}{{println .}}{{end}}' |
    Where-Object { $_ -like "AI_PRIMARY_MODEL=*" } |
    Select-Object -First 1
if ($ProductionModel -ne "AI_PRIMARY_MODEL=qwen2.5:3b") {
    throw "Production primary model changed during evaluation."
}

Write-Host ""
Write-Host "P2-01 validation PASSED."
Write-Host "Models evaluated: $($Data.models -join ', ')"
Write-Host "Total generation runs: $($Data.total_runs)"
Write-Host "Paid API credits: $($Data.paid_api_credits)"
Write-Host "Production model: qwen2.5:3b (unchanged)"
