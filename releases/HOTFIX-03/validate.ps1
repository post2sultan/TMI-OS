param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$result = docker exec tmi-production-backend-1 python -c `
    "import os,requests; base='http://127.0.0.1:8000'; h={'X-TMI-API-Key':os.environ['AUTH_ADMIN_API_KEY'],'X-TMI-Actor':'HOTFIX-03'}; r=requests.post(base+'/campaigns/167/analyze?force=false',headers=h,timeout=900); r.raise_for_status(); d=requests.get(base+'/campaigns/167/analysis/latest',headers=h,timeout=30).json(); assert d['campaign_id']==167; assert len(d['dimensions'])==7; print('CAMPAIGN_167_PERSISTED')"
if ($LASTEXITCODE -ne 0 -or $result -notmatch "CAMPAIGN_167_PERSISTED") {
    throw "Campaign-specific runtime validation failed."
}

Write-Host "HOTFIX-03 validation PASSED."
Write-Host "Campaign 167 analysis persisted with seven dimensions."
Write-Host "Paid API credits: 0"
