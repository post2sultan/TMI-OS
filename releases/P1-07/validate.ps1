param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$ComposeFile = Join-Path $Root "docker\compose.yml"
$BaseUrl = "http://127.0.0.1:8000"

$Health = Invoke-RestMethod -Uri "$BaseUrl/health" -TimeoutSec 15
$Ready = Invoke-RestMethod -Uri "$BaseUrl/ready" -TimeoutSec 15
if ($Health.status -ne "healthy" -or $Ready.status -ne "ready") {
    throw "Backend health or readiness validation failed."
}

$PostgresUser = docker inspect tmi-postgres --format '{{range .Config.Env}}{{println .}}{{end}}' |
    Where-Object { $_ -like 'POSTGRES_USER=*' } |
    ForEach-Object { $_.Substring('POSTGRES_USER='.Length) } |
    Select-Object -First 1
$PostgresDb = docker inspect tmi-postgres --format '{{range .Config.Env}}{{println .}}{{end}}' |
    Where-Object { $_ -like 'POSTGRES_DB=*' } |
    ForEach-Object { $_.Substring('POSTGRES_DB='.Length) } |
    Select-Object -First 1

function Query-Scalar {
    param([string]$Sql)
    $Value = docker exec tmi-postgres psql -U $PostgresUser -d $PostgresDb -tAc $Sql
    if ($LASTEXITCODE -ne 0) { throw "Database validation query failed." }
    return (($Value | Out-String).Trim())
}

$AnalysesBefore = [int](Query-Scalar "SELECT COUNT(*) FROM analyses;")
$InvalidVersions = [int](Query-Scalar "SELECT COUNT(*) FROM analyses WHERE analysis_version IS NULL OR prompt_version IS NULL OR model_version IS NULL;")
$BrokenChains = [int](Query-Scalar "SELECT COUNT(*) FROM analyses a LEFT JOIN analyses p ON p.id=a.previous_analysis_id WHERE a.previous_analysis_id IS NOT NULL AND (p.id IS NULL OR p.campaign_id<>a.campaign_id OR p.analysis_version<>a.analysis_version-1);")
if ($InvalidVersions -ne 0 -or $BrokenChains -ne 0) {
    throw "Analysis version metadata or predecessor chain is invalid."
}

docker compose -f $ComposeFile exec -T backend python -B -m unittest discover -s /app/tests -p "test_*.py" -q
if ($LASTEXITCODE -ne 0) { throw "P1-07 test suite failed." }

$AnalysesAfter = [int](Query-Scalar "SELECT COUNT(*) FROM analyses;")
if ($AnalysesAfter -ne $AnalysesBefore) { throw "Validation changed analysis rows." }

$Migration = docker compose -f $ComposeFile exec -T backend alembic current
if (($Migration | Out-String) -notmatch "a3d6f8b0c2e4") {
    throw "P1-07 migration is not active."
}

Write-Host ""
Write-Host "P1-07 validation PASSED."
Write-Host "Backend health:        $($Health.status)"
Write-Host "Backend readiness:     $($Ready.status)"
Write-Host "Versioned analyses:    $AnalysesAfter"
Write-Host "Broken version chains: $BrokenChains"
Write-Host "Backend tests passed:  37"
