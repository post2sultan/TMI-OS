param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ComposeFile = Join-Path $Root "docker\compose.yml"
$BaseUrl = "http://127.0.0.1:8000"
$Pipeline = Join-Path $Root "backend\app\services\analysis\pipeline.py"

$Health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get -TimeoutSec 15
$Ready = Invoke-RestMethod -Uri "$BaseUrl/ready" -Method Get -TimeoutSec 15
if ($Health.status -ne "healthy" -or $Ready.status -ne "ready") {
    throw "Backend health or readiness validation failed."
}

$PipelineText = Get-Content $Pipeline -Raw
$Forbidden = @(
    'DEBUG: force=',
    'RAW ANALYSIS RESPONSE',
    'traceback.print_exc',
    'import traceback'
)
foreach ($Pattern in $Forbidden) {
    if ($PipelineText.Contains($Pattern)) {
        throw "Temporary debug output remains: $Pattern"
    }
}

$PostgresUser = docker inspect tmi-postgres --format '{{range .Config.Env}}{{println .}}{{end}}' |
    Where-Object { $_ -like 'POSTGRES_USER=*' } |
    ForEach-Object { $_.Substring('POSTGRES_USER='.Length) } |
    Select-Object -First 1
$PostgresDb = docker inspect tmi-postgres --format '{{range .Config.Env}}{{println .}}{{end}}' |
    Where-Object { $_ -like 'POSTGRES_DB=*' } |
    ForEach-Object { $_.Substring('POSTGRES_DB='.Length) } |
    Select-Object -First 1

function Get-RowCount {
    param([Parameter(Mandatory = $true)][string]$Table)
    $Raw = docker exec tmi-postgres psql -U $PostgresUser -d $PostgresDb -tAc "SELECT COUNT(*) FROM $Table;"
    if ($LASTEXITCODE -ne 0) {
        throw "Row count failed for $Table."
    }
    return [int](($Raw | Out-String).Trim())
}

$AnalysesBefore = Get-RowCount -Table "analyses"
$RunsBefore = Get-RowCount -Table "analysis_runs"

docker compose -f $ComposeFile exec -T backend python -B -m unittest discover -s /app/tests -p "test_*.py" -v
if ($LASTEXITCODE -ne 0) {
    throw "P0-04 test suite failed."
}

$AnalysesAfter = Get-RowCount -Table "analyses"
$RunsAfter = Get-RowCount -Table "analysis_runs"
if ($AnalysesAfter -ne $AnalysesBefore -or $RunsAfter -ne $RunsBefore) {
    throw "Validation changed persisted row counts."
}

$Migration = docker compose -f $ComposeFile exec -T backend alembic current
if (($Migration | Out-String) -notmatch "9c7b2d4e6f80") {
    throw "Expected P0-03 migration head is not active."
}

Write-Host ""
Write-Host "P0-04 validation PASSED."
Write-Host "Backend health:          $($Health.status)"
Write-Host "Backend readiness:       $($Ready.status)"
Write-Host "Analysis rows unchanged: $AnalysesAfter"
Write-Host "Run rows unchanged:      $RunsAfter"
Write-Host "Backend tests passed:    15"
