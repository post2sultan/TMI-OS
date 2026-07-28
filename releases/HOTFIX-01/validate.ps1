param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Health = docker inspect tmi-production-backend-1 `
    --format "{{.State.Health.Status}}"
if (($Health | Out-String).Trim() -ne "healthy") {
    throw "Production backend is not healthy."
}

docker exec tmi-production-backend-1 python -B -c `
    "from app.core.database import SessionLocal; from app.models.analysis_run import AnalysisRun; from app.models.campaign import Campaign; from app.services.analysis.parser import analysis_parser; from app.services.analysis.quality_validator import analysis_quality_validator; d=SessionLocal(); r=d.get(AnalysisRun,22); c=d.get(Campaign,r.campaign_id); a=analysis_parser.parse(r.raw_response); q=analysis_quality_validator.validate(a,(c.title,)); assert q.is_valid,q.errors; print('STORED_RESPONSE_PASSED'); d.close()"
if ($LASTEXITCODE -ne 0) {
    throw "Stored production response validation failed."
}

Write-Host "HOTFIX-01 validation PASSED."
Write-Host "New AI generations: 0"
Write-Host "Paid API credits: 0"
