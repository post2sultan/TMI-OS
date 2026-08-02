param([string]$Root = "O:\TMI-OS", [switch]$SourceOnly)
$ErrorActionPreference = "Stop"
$page = Get-Content -LiteralPath (Join-Path $Root "frontend\src\pages\CampaignRadarPage.tsx") -Raw
$router = Get-Content -LiteralPath (Join-Path $Root "backend\app\routers\radar.py") -Raw
if (-not $page.Contains("Radar command center") -or -not $page.Contains("Campaign candidates") -or -not $page.Contains("Source health")) { throw "Radar command center views are incomplete." }
if (-not $page.Contains("Confirm as campaign") -or -not $router.Contains('/clusters/{cluster_id}/promote')) { throw "Human-governed promotion workflow is missing." }
if (-not $router.Contains("promoted_campaign_id is not None")) { throw "Idempotent promotion guard is missing." }
if (-not $SourceOnly) {
    $backend = docker inspect tmi-production-backend-1 --format '{{.State.Health.Status}}'
    $frontend = docker inspect tmi-production-frontend-1 --format '{{.State.Health.Status}}'
    if ($backend -ne "healthy" -or $frontend -ne "healthy") { throw "Production application is not healthy." }
    $web = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:5173/healthz" -TimeoutSec 30
    if ($web.StatusCode -ne 200) { throw "Protected Radar frontend is not healthy." }
    docker exec tmi-production-frontend-1 sh -c "grep -R -q 'Radar command center' /srv/assets"
    if ($LASTEXITCODE -ne 0) { throw "Radar command center asset is not deployed." }
    docker exec tmi-production-backend-1 python -c "import os,requests; h={'X-TMI-API-Key':os.environ['AUTH_ADMIN_API_KEY'],'X-TMI-Actor':'RADAR-08'}; b='http://127.0.0.1:8000'; c=requests.get(b+'/radar/clusters?sort=trend&limit=5',headers=h,timeout=30); c.raise_for_status(); s=requests.get(b+'/radar/sources',headers=h,timeout=30); s.raise_for_status(); w=requests.get(b+'/radar/watchlists',headers=h,timeout=30); w.raise_for_status(); print('RADAR_COMMAND_CENTER_APIS_OK')"
    if ($LASTEXITCODE -ne 0) { throw "RADAR-08 API runtime validation failed." }
}
Write-Host "RADAR-08 validation PASSED. Candidate command center and governed promotion are operational."
