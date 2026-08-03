param([string]$Root = "O:\TMI-OS", [switch]$SourceOnly)
$ErrorActionPreference = "Stop"
$page = Get-Content -LiteralPath (Join-Path $Root "frontend\src\pages\CampaignRadarPage.tsx") -Raw
$router = Get-Content -LiteralPath (Join-Path $Root "backend\app\routers\radar.py") -Raw
if (-not $page.Contains("Latest scan results") -or -not $page.Contains("listRadarClustersByIds")) { throw "Latest-scan result view is missing." }
if (-not $router.Contains("_parse_cluster_ids") -or -not $router.Contains("CampaignCluster.id.in_(selected_ids)")) { throw "Safe cluster selection is missing." }
if (-not $SourceOnly) {
    docker exec tmi-production-frontend-1 sh -c "grep -R -q 'Latest scan results' /srv/assets"
    if ($LASTEXITCODE -ne 0) { throw "Latest scan view is not deployed." }
    docker exec tmi-production-backend-1 python -c "from app.routers.radar import _parse_cluster_ids; assert _parse_cluster_ids('3,2,bad,3') == [3,2]; print('RADAR_LATEST_SCAN_RUNTIME_OK')"
    if ($LASTEXITCODE -ne 0) { throw "Latest scan API runtime validation failed." }
}
Write-Host "RADAR-09 validation PASSED."
