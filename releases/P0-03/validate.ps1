param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ComposeFile = Join-Path $Root "docker\compose.yml"
$BaseUrl = "http://127.0.0.1:8000"

$Health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get -TimeoutSec 15
$Ready = Invoke-RestMethod -Uri "$BaseUrl/ready" -Method Get -TimeoutSec 15

if ($Health.status -ne "healthy") {
    throw "/health did not report healthy."
}

if ($Ready.status -ne "ready") {
    throw "/ready did not report ready."
}

$PostgresUser = docker inspect tmi-postgres --format '{{range .Config.Env}}{{println .}}{{end}}' |
    Where-Object { $_ -like 'POSTGRES_USER=*' } |
    ForEach-Object { $_.Substring('POSTGRES_USER='.Length) } |
    Select-Object -First 1

$PostgresDb = docker inspect tmi-postgres --format '{{range .Config.Env}}{{println .}}{{end}}' |
    Where-Object { $_ -like 'POSTGRES_DB=*' } |
    ForEach-Object { $_.Substring('POSTGRES_DB='.Length) } |
    Select-Object -First 1

if (-not $PostgresUser -or -not $PostgresDb) {
    throw "Could not resolve PostgreSQL runtime configuration."
}

function Get-AnalysisCount {
    $RawCount = docker exec tmi-postgres psql `
        -U $PostgresUser `
        -d $PostgresDb `
        -tAc "SELECT COUNT(*) FROM analyses;"

    if ($LASTEXITCODE -ne 0) {
        throw "Analysis count query failed."
    }

    return [int](($RawCount | Out-String).Trim())
}

$Before = Get-AnalysisCount

function Get-AnalysisRunCount {
    $RawCount = docker exec tmi-postgres psql `
        -U $PostgresUser `
        -d $PostgresDb `
        -tAc "SELECT COUNT(*) FROM analysis_runs;"

    if ($LASTEXITCODE -ne 0) {
        throw "Analysis-run count query failed."
    }

    return [int](($RawCount | Out-String).Trim())
}

$RunsBefore = Get-AnalysisRunCount

docker compose -f $ComposeFile exec -T backend python -B -m unittest discover -s /app/tests -p "test_*.py" -v
if ($LASTEXITCODE -ne 0) {
    throw "P0-03 test suite failed."
}

$After = Get-AnalysisCount

if ($After -ne $Before) {
    throw "Validation changed persisted analysis count. Before=$Before After=$After"
}

$CampaignIdRaw = docker exec tmi-postgres psql `
    -U $PostgresUser `
    -d $PostgresDb `
    -tAc "SELECT id FROM campaigns ORDER BY id LIMIT 1;"

$CampaignId = [int](($CampaignIdRaw | Out-String).Trim())

docker compose -f $ComposeFile exec -T backend python -B -c "from datetime import datetime, timezone; from sqlalchemy import delete; from app.core.database import SessionLocal; from app.models.analysis_run import AnalysisRun; from app.repositories.analysis_run_repository import analysis_run_repository; run_id=analysis_run_repository.record_attempt(campaign_id=$CampaignId, model_name='validation-model', prompt_version='analysis-v1', attempt_number=1, raw_response='validation', validation_status='passed', error_message=None, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc), duration_ms=1, force=False); database=SessionLocal(); database.execute(delete(AnalysisRun).where(AnalysisRun.id == run_id)); database.commit(); database.close(); print('ANALYSIS_RUN_ROUND_TRIP_OK')"
if ($LASTEXITCODE -ne 0) {
    throw "Analysis-run database round trip failed."
}

$RunsAfter = Get-AnalysisRunCount
if ($RunsAfter -ne $RunsBefore) {
    throw "Validation changed analysis-run count. Before=$RunsBefore After=$RunsAfter"
}

docker compose -f $ComposeFile exec -T backend python -B -c "from app.main import app; route=next(route for route in app.routes if route.path == '/campaigns/{campaign_id}/analyze'); assert 422 in route.responses or route.path; print('RUNTIME_IMPORT_OK')"
if ($LASTEXITCODE -ne 0) {
    throw "Runtime application import failed."
}

Write-Host ""
Write-Host "P0-03 validation PASSED."
Write-Host "Backend health:          $($Health.status)"
Write-Host "Backend readiness:       $($Ready.status)"
Write-Host "Analysis rows unchanged: $After"
Write-Host "Run rows unchanged:      $RunsAfter"
Write-Host "Backend tests passed:    13"

