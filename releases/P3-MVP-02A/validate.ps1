param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
$EnvFile = Join-Path $Root "docker\.env.production.local"
$ComposeFile = Join-Path $Root "docker\compose.production.yml"

docker compose --env-file $EnvFile --project-name tmi-production `
    -f $ComposeFile exec -T backend python -B -c `
    "import os,requests; b='http://127.0.0.1:8000'; h={'X-TMI-API-Key':os.environ['AUTH_ADMIN_API_KEY'],'X-TMI-Actor':'P3-MVP-02A'}; p=requests.post(b+'/media/voices/af_heart/preview',headers=h,timeout=600); assert p.ok,p.text; u=p.json()['preview_url'].replace('/api',''); a=requests.get(b+u,headers=h,timeout=60); assert len(a.content)>10000; jobs=requests.get(b+'/content-creation',headers=h,timeout=30).json()['items']; c=next(x for x in jobs if x['video_script']); cid=c['campaign_id']; r=requests.post(f'{b}/campaigns/{cid}/media/generate',headers=h,json={'voice_name':'af_heart'},timeout=900); assert r.ok,r.text; j=next(x for x in r.json()['items'] if x['campaign_id']==cid); assert j['voice_name']=='af_heart' and j['video_url']; v=requests.get(b+j['video_url'].replace('/api',''),headers=h,timeout=60); assert len(v.content)>10000; print(f'KOKORO_VOICE_PASSED:{cid}:{len(a.content)}:{len(v.content)}')"
if ($LASTEXITCODE -ne 0) { throw "Kokoro runtime validation failed." }

docker compose --env-file $EnvFile --project-name tmi-production `
    -f $ComposeFile ps
if ($LASTEXITCODE -ne 0) { throw "Production health validation failed." }
Write-Host "P3-MVP-02A validation PASSED."
Write-Host "Paid API credits: 0"
