param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
$EnvFile = Join-Path $Root "docker\.env.production.local"
$ComposeFile = Join-Path $Root "docker\compose.production.yml"
docker compose --env-file $EnvFile --project-name tmi-production -f $ComposeFile exec -T backend python -B -c `
    "import io,os,requests,zipfile; b='http://127.0.0.1:8000'; h={'X-TMI-API-Key':os.environ['AUTH_ADMIN_API_KEY'],'X-TMI-Actor':'P3-MVP-04'}; jobs=requests.get(b+'/content-creation',headers=h,timeout=30).json()['items']; c=next(x for x in jobs if x['video_url']); cid=c['campaign_id']; r=requests.post(f'{b}/campaigns/{cid}/social/export',headers=h,timeout=900); assert r.ok,r.text; j=next(x for x in r.json()['items'] if x['campaign_id']==cid); z=requests.get(b+j['social_export_url'].replace('/api',''),headers=h,timeout=120); z.raise_for_status(); a=zipfile.ZipFile(io.BytesIO(z.content)); required={'youtube/video.mp4','youtube/shorts.mp4','instagram/reel.mp4','instagram/story.mp4','tiktok/reel.mp4','linkedin/post.mp4','manifest.json'}; assert required<=set(a.namelist()); assert all(a.getinfo(n).file_size>10000 for n in required if n.endswith('.mp4')); print(f'CHANNEL_RENDERS_PASSED:{cid}:{len(z.content)}')"
if ($LASTEXITCODE -ne 0) { throw "Channel render validation failed." }
docker compose --env-file $EnvFile --project-name tmi-production -f $ComposeFile ps
Write-Host "P3-MVP-04 validation PASSED."
Write-Host "Paid API credits: 0"
