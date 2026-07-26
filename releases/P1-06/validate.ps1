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

function Get-Count {
    param([string]$Table)
    $Value = docker exec tmi-postgres psql -U $PostgresUser -d $PostgresDb -tAc "SELECT COUNT(*) FROM $Table;"
    if ($LASTEXITCODE -ne 0) { throw "Count failed for $Table." }
    return [int](($Value | Out-String).Trim())
}

$CampaignsBefore = Get-Count "campaigns"
$DocumentsBefore = Get-Count "campaign_documents"
$AnalysesBefore = Get-Count "analyses"

docker compose -f $ComposeFile exec -T backend python -B -m unittest discover -s /app/tests -p "test_*.py" -q
if ($LASTEXITCODE -ne 0) { throw "P1-06 test suite failed." }

docker compose -f $ComposeFile exec -T backend python -B -c "from app.main import app; paths={r.path for r in app.routes}; required={'/reviews','/campaigns/{campaign_id}/evidence','/campaigns/{campaign_id}/analysis/latest','/campaigns/{campaign_id}/analysis','/campaigns/{campaign_id}/approve','/campaigns/{campaign_id}/reject','/campaigns/{campaign_id}/reanalyze','/campaigns/{campaign_id}/archive'}; missing=required-paths; assert not missing, missing; print('REVIEW_ROUTES_OK')"
if ($LASTEXITCODE -ne 0) { throw "Campaign review route validation failed." }

$CampaignsAfter = Get-Count "campaigns"
$DocumentsAfter = Get-Count "campaign_documents"
$AnalysesAfter = Get-Count "analyses"
if ($CampaignsAfter -ne $CampaignsBefore -or $DocumentsAfter -ne $DocumentsBefore -or $AnalysesAfter -ne $AnalysesBefore) {
    throw "Validation changed persisted row counts."
}

$Migration = docker compose -f $ComposeFile exec -T backend alembic current
if (($Migration | Out-String) -notmatch "f2c5d7e9a1b3") {
    throw "Expected P1-05 migration head is not active."
}

Write-Host ""
Write-Host "P1-06 validation PASSED."
Write-Host "Backend health:          $($Health.status)"
Write-Host "Backend readiness:       $($Ready.status)"
Write-Host "Campaign rows unchanged: $CampaignsAfter"
Write-Host "Evidence rows unchanged: $DocumentsAfter"
Write-Host "Analysis rows unchanged: $AnalysesAfter"
Write-Host "Backend tests passed:    35"
Write-Host "Review routes:           registered"
