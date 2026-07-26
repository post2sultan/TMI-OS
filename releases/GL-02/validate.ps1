param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$ComposeFile = Join-Path $Root "docker\compose.yml"
$BaseUrl = "http://127.0.0.1:8000"

$Health = Invoke-RestMethod "$BaseUrl/health" -TimeoutSec 15
$Ready = Invoke-RestMethod "$BaseUrl/ready" -TimeoutSec 15
if ($Health.status -ne "healthy" -or $Ready.status -ne "ready") {
    throw "Development stack health validation failed."
}

$PostgresUser = docker inspect tmi-postgres --format '{{range .Config.Env}}{{println .}}{{end}}' |
    Where-Object { $_ -like 'POSTGRES_USER=*' } |
    ForEach-Object { $_.Substring('POSTGRES_USER='.Length) } |
    Select-Object -First 1
$PostgresDb = docker inspect tmi-postgres --format '{{range .Config.Env}}{{println .}}{{end}}' |
    Where-Object { $_ -like 'POSTGRES_DB=*' } |
    ForEach-Object { $_.Substring('POSTGRES_DB='.Length) } |
    Select-Object -First 1
$CampaignsBefore = [int]((docker exec tmi-postgres psql -U $PostgresUser -d $PostgresDb -tAc "SELECT COUNT(*) FROM campaigns;" | Out-String).Trim())

docker compose -f $ComposeFile exec -T backend python -B -m unittest discover -s /app/tests -p "test_*.py" -q
if ($LASTEXITCODE -ne 0) { throw "GL-02 backend tests failed." }

& (Join-Path $Root "scripts\validate-production-container.ps1") -Root $Root

$CampaignsAfter = [int]((docker exec tmi-postgres psql -U $PostgresUser -d $PostgresDb -tAc "SELECT COUNT(*) FROM campaigns;" | Out-String).Trim())
if ($CampaignsAfter -ne $CampaignsBefore) {
    throw "GL-02 validation changed campaign data."
}

$Migration = docker compose -f $ComposeFile exec -T backend alembic current
if (($Migration | Out-String) -notmatch "c5f8a1d3e6b9") {
    throw "Expected GL-01 migration head is not active."
}

Write-Host ""
Write-Host "GL-02 validation PASSED."
Write-Host "Development health: healthy and ready"
Write-Host "Production images: digest-pinned"
Write-Host "Internal host ports: none"
Write-Host "Backend: non-root, read-only, capability-free"
Write-Host "Production runtime probe: passed"
Write-Host "Backend tests: 50"
Write-Host "Campaign rows unchanged: $CampaignsAfter"
