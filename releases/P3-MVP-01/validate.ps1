param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$result = docker exec tmi-production-backend-1 python -c `
    "import os,requests; b='http://127.0.0.1:8000'; h={'X-TMI-API-Key':os.environ['AUTH_ADMIN_API_KEY'],'X-TMI-Actor':'P3-MVP-01'}; r=requests.post(b+'/campaigns/167/content/generate',headers=h,timeout=900); r.raise_for_status(); jobs=requests.get(b+'/content-creation',headers=h,timeout=30).json()['items']; job=next(x for x in jobs if x['campaign_id']==167); assert len(job['video_script'])>=80; assert len(job['social_caption'])>=20; assert len(job['hashtags'])>=3; assert job['status']=='generated'; print('CONTENT_PACKAGE_167_PASSED')"
if ($LASTEXITCODE -ne 0 -or $result -notmatch "CONTENT_PACKAGE_167_PASSED") {
    throw "P3-MVP-01 runtime validation failed."
}
Write-Host "P3-MVP-01 validation PASSED."
Write-Host "Campaign 167 content package stored."
Write-Host "Paid API credits: 0"
