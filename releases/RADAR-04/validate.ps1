param([string]$Root = "O:\TMI-OS", [switch]$SourceOnly)
$ErrorActionPreference = "Stop"
$service = Get-Content -LiteralPath (Join-Path $Root "backend\app\services\radar_signal_service.py") -Raw
$frontend = Get-Content -LiteralPath (Join-Path $Root "frontend\src\lib\api.ts") -Raw
if (-not $service.Contains("DiscoverySignal") -or -not $service.Contains("CampaignCluster")) { throw "Signal-to-cluster service is incomplete." }
if (-not $service.Contains('"corroborated"')) { throw "Corroboration state is missing." }
if (-not $frontend.Contains('"/radar/discover"')) { throw "Dashboard still uses URL-to-campaign discovery." }
if (-not $SourceOnly) {
    $backend = docker inspect tmi-production-backend-1 --format '{{.State.Health.Status}}'
    $frontendStatus = docker inspect tmi-production-frontend-1 --format '{{.State.Health.Status}}'
    if ($backend -ne "healthy" -or $frontendStatus -ne "healthy") { throw "Production services are not healthy." }
    docker exec tmi-production-backend-1 python -c "from app.models.discovery_signal import DiscoverySignal; from app.models.campaign_cluster import CampaignCluster; print('RADAR_MODELS_OK')"
    if ($LASTEXITCODE -ne 0) { throw "RADAR-04 runtime model import failed." }
    docker exec tmi-production-backend-1 python -c "import os,requests; h={'X-TMI-API-Key':os.environ['AUTH_ADMIN_API_KEY'],'X-TMI-Actor':'RADAR-04'}; r=requests.get('http://127.0.0.1:8000/radar/clusters',headers=h,timeout=30); r.raise_for_status(); d=r.json(); assert 'items' in d and 'total' in d; print('RADAR_API_OK')"
    if ($LASTEXITCODE -ne 0) { throw "RADAR-04 runtime API validation failed." }
}
Write-Host "RADAR-04 validation PASSED. Signals are separated from campaigns."
