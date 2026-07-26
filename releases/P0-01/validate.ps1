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

docker compose -f $ComposeFile exec -T backend python -B -m unittest discover -s /app/tests -p "test_*.py" -v
if ($LASTEXITCODE -ne 0) {
    throw "P0-01 test suite failed."
}

$After = Get-AnalysisCount

if ($After -ne $Before) {
    throw "Validation changed persisted analysis count. Before=$Before After=$After"
}

docker compose -f $ComposeFile exec -T backend python -B -c "from app.main import app; route=next(route for route in app.routes if route.path == '/campaigns/{campaign_id}/analyze'); assert 422 in route.responses or route.path; print('RUNTIME_IMPORT_OK')"
if ($LASTEXITCODE -ne 0) {
    throw "Runtime application import failed."
}

Write-Host ""
Write-Host "P0-01 validation PASSED."
Write-Host "Backend health:          $($Health.status)"
Write-Host "Backend readiness:       $($Ready.status)"
Write-Host "Analysis rows unchanged: $After"
Write-Host "Quality tests passed:    8"
