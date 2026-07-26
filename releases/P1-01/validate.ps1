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

$Campaigns = Get-Count "campaigns"
$DocumentsBefore = Get-Count "campaign_documents"
if ($DocumentsBefore -lt $Campaigns) {
    throw "Not every existing campaign was backfilled."
}

docker compose -f $ComposeFile exec -T backend python -B -m unittest discover -s /app/tests -p "test_*.py" -v
if ($LASTEXITCODE -ne 0) { throw "P1-01 test suite failed." }

$CampaignIdRaw = docker exec tmi-postgres psql -U $PostgresUser -d $PostgresDb -tAc "SELECT id FROM campaigns ORDER BY id LIMIT 1;"
$CampaignId = [int](($CampaignIdRaw | Out-String).Trim())
docker compose -f $ComposeFile exec -T backend python -B -c "from app.core.database import SessionLocal; from app.models.campaign_document import CampaignDocument; from app.repositories.campaign_document_repository import campaign_document_repository; db=SessionLocal(); item=campaign_document_repository.create(session=db,campaign_id=$CampaignId,document_type='manual_observation',title='P1-01 validation',content='temporary'); db.flush(); item_id=item.id; db.rollback(); assert db.get(CampaignDocument,item_id) is None; db.close(); print('DOCUMENT_ROUND_TRIP_OK')"
if ($LASTEXITCODE -ne 0) { throw "Document rollback round trip failed." }

$DocumentsAfter = Get-Count "campaign_documents"
if ($DocumentsAfter -ne $DocumentsBefore) {
    throw "Validation changed document count."
}

$Migration = docker compose -f $ComposeFile exec -T backend alembic current
if (($Migration | Out-String) -notmatch "b8e1f2a3c4d5") {
    throw "P1-01 migration is not active."
}

Write-Host ""
Write-Host "P1-01 validation PASSED."
Write-Host "Backend health:             $($Health.status)"
Write-Host "Backend readiness:          $($Ready.status)"
Write-Host "Campaigns backfilled:       $Campaigns"
Write-Host "Document rows unchanged:    $DocumentsAfter"
Write-Host "Backend tests passed:       19"
