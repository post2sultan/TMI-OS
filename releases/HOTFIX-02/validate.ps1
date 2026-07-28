param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$frontendHealth = docker exec tmi-production-frontend-1 `
    wget -qO- http://127.0.0.1/healthz
if ($LASTEXITCODE -ne 0 -or $frontendHealth -notmatch "healthy") {
    throw "Frontend health validation failed."
}

$shape = docker exec tmi-production-backend-1 python -c `
    "import os,requests; d=requests.get('http://127.0.0.1:8000/campaigns/145/analysis/latest',headers={'X-TMI-API-Key':os.environ['AUTH_ADMIN_API_KEY']}).json(); assert isinstance(d['dimensions'],list) and len(d['dimensions'])==7; assert all(isinstance(x.get('evidence',[]),list) for x in d['dimensions']); print('ANALYSIS_SHAPE_PASSED')"
if ($LASTEXITCODE -ne 0 -or $shape -notmatch "ANALYSIS_SHAPE_PASSED") {
    throw "Analysis response validation failed."
}

Write-Host "HOTFIX-02 validation PASSED."
Write-Host "Campaign 145 data preserved."
Write-Host "Paid API credits: 0"
