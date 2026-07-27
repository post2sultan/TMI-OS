param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Results = Join-Path $Root "releases\P2-01A\results\evaluation.json"
if (-not (Test-Path $Results)) {
    throw "P2-01A evaluation results are missing."
}
$Data = Get-Content -LiteralPath $Results -Raw | ConvertFrom-Json

if ($Data.total_runs -ne 4 -or $Data.runs_per_model -ne 2) {
    throw "P2-01A exceeded or missed its four-run ceiling."
}
if ($Data.paid_api_credits -ne 0 -or $Data.production_model_changed) {
    throw "P2-01A violated its cost or production invariance gate."
}

$PassingModels = @(
    $Data.models |
        Where-Object {
            $Summary = $Data.summaries.$_
            $Summary.valid_runs -eq 2
        }
)
if ($PassingModels.Count -lt 1) {
    throw "Prompt v2 did not produce two valid runs for any model."
}

$ProductionModel = docker inspect tmi-production-backend-1 `
    --format '{{range .Config.Env}}{{println .}}{{end}}' |
    Where-Object { $_ -like "AI_PRIMARY_MODEL=*" } |
    Select-Object -First 1
if ($ProductionModel -ne "AI_PRIMARY_MODEL=qwen2.5:3b") {
    throw "Production model changed during prompt evaluation."
}

Write-Host ""
Write-Host "P2-01A validation PASSED."
Write-Host "Passing models: $($PassingModels -join ', ')"
Write-Host "Total generation runs: $($Data.total_runs)"
Write-Host "Paid API credits: 0"
Write-Host "Production model: qwen2.5:3b (unchanged)"
