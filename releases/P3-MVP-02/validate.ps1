param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
$EnvFile = Join-Path $Root "docker\.env.production.local"
$ComposeFile = Join-Path $Root "docker\compose.production.yml"

docker compose --env-file $EnvFile --project-name tmi-production `
    -f $ComposeFile exec -T backend python -B -c `
    "import os,requests; b='http://127.0.0.1:8000'; h={'X-TMI-API-Key':os.environ['AUTH_ADMIN_API_KEY'],'X-TMI-Actor':'P3-MVP-02'}; jobs=requests.get(b+'/content-creation',headers=h,timeout=30).json()['items']; candidate=next((x for x in jobs if x['video_script']),None); assert candidate,'No generated script exists'; cid=candidate['campaign_id']; r=requests.post(f'{b}/campaigns/{cid}/media/generate',headers=h,timeout=900); r.raise_for_status(); job=next(x for x in r.json()['items'] if x['campaign_id']==cid); assert job['audio_url'] and job['video_url']; a=requests.get(b+job['audio_url'].replace('/api',''),headers=h,timeout=60); v=requests.get(b+job['video_url'].replace('/api',''),headers=h,timeout=60); assert a.status_code==200 and len(a.content)>1000; assert v.status_code==200 and len(v.content)>10000; print(f'LOCAL_VIDEO_PASSED:{cid}:{len(v.content)}')"
if ($LASTEXITCODE -ne 0) { throw "Real media runtime validation failed." }

docker compose --env-file $EnvFile --project-name tmi-production `
    -f $ComposeFile ps
if ($LASTEXITCODE -ne 0) { throw "Production health validation failed." }

Write-Host "P3-MVP-02 validation PASSED."
Write-Host "Paid API credits: 0"
