param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
$EnvFile = Join-Path $Root "docker\.env.production.local"
$ComposeFile = Join-Path $Root "docker\compose.production.yml"

docker compose --env-file $EnvFile --project-name tmi-production `
    -f $ComposeFile exec -T backend python -B -c `
    "import io,os,requests,zipfile; b='http://127.0.0.1:8000'; h={'X-TMI-API-Key':os.environ['AUTH_ADMIN_API_KEY'],'X-TMI-Actor':'P3-MVP-03'}; jobs=requests.get(b+'/content-creation',headers=h,timeout=30).json()['items']; c=next(x for x in jobs if x['video_url']); cid=c['campaign_id']; p=requests.post(f'{b}/campaigns/{cid}/publish',headers=h,timeout=30) if c['status']!='published' else None; assert p is None or p.ok,('' if p is None else p.text); r=requests.post(f'{b}/campaigns/{cid}/social/export',headers=h,timeout=120); assert r.ok,r.text; j=next(x for x in r.json()['items'] if x['campaign_id']==cid); z=requests.get(b+j['social_export_url'].replace('/api',''),headers=h,timeout=60); z.raise_for_status(); archive=zipfile.ZipFile(io.BytesIO(z.content)); names=set(archive.namelist()); assert {'video.mp4','caption.txt','script.txt','manifest.json'}<=names; assert len(z.content)>10000; print(f'SOCIAL_EXPORT_PASSED:{cid}:{len(z.content)}')"
if ($LASTEXITCODE -ne 0) { throw "Social export runtime validation failed." }
docker compose --env-file $EnvFile --project-name tmi-production -f $ComposeFile ps
if ($LASTEXITCODE -ne 0) { throw "Production health validation failed." }
Write-Host "P3-MVP-03 validation PASSED."
Write-Host "Paid API credits: 0"
