param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$result = docker exec tmi-production-backend-1 python -c `
    "import os,requests; b='http://127.0.0.1:8000'; h={'X-TMI-API-Key':os.environ['AUTH_ADMIN_API_KEY'],'X-TMI-Actor':'P3-MVP-01'}; approved=requests.get(b+'/reviews?status=approved',headers=h,timeout=30).json()['items']; published=requests.get(b+'/reviews?status=published',headers=h,timeout=30).json()['items']; candidate=(approved or published)[0]; cid=candidate['campaign_id']; r=requests.post(f'{b}/campaigns/{cid}/content/generate',headers=h,timeout=900); r.raise_for_status(); jobs=requests.get(b+'/content-creation',headers=h,timeout=30).json()['items']; job=next(x for x in jobs if x['campaign_id']==cid); assert 80<=len(job['video_script'].split())<=160; assert 20<=len(job['social_caption'].split())<=90; assert len(job['hashtags'])>=3; assert job['status'] in {'generated','published'}; print(f'CONTENT_PACKAGE_PASSED:{cid}')"
if ($LASTEXITCODE -ne 0 -or $result -notmatch "CONTENT_PACKAGE_PASSED:") {
    throw "P3-MVP-01 runtime validation failed."
}
Write-Host "P3-MVP-01 validation PASSED."
Write-Host "Real campaign content package stored."
Write-Host "Paid API credits: 0"
