param([string]$Root = "O:\TMI-OS", [switch]$SourceOnly)
$ErrorActionPreference = "Stop"
$monitor = Get-Content -LiteralPath (Join-Path $Root "backend\app\services\radar_source_monitor.py") -Raw
$router = Get-Content -LiteralPath (Join-Path $Root "backend\app\routers\radar.py") -Raw
if (-not $monitor.Contains("max_sources_per_run = 10") -or -not $monitor.Contains("max_items_per_source = 50")) { throw "Radar monitoring ceilings are missing." }
if (-not $monitor.Contains('source_type in {"rss", "atom"}') -or -not $monitor.Contains('source.source_type == "sitemap"')) { throw "Free multi-source collectors are incomplete." }
if (-not $router.Contains('/sources') -or -not $router.Contains('/monitor/run')) { throw "Radar source-health API is incomplete." }
if (-not (Test-Path (Join-Path $Root "tools\radar\run-monitor.ps1"))) { throw "Radar monitor runner is missing." }
if (-not $SourceOnly) {
    $backend = docker inspect tmi-production-backend-1 --format '{{.State.Health.Status}}'
    if ($backend -ne "healthy") { throw "Production backend is not healthy." }
    docker exec tmi-production-backend-1 python -c "import os,requests; h={'X-TMI-API-Key':os.environ['AUTH_ADMIN_API_KEY'],'X-TMI-Actor':'RADAR-06'}; r=requests.get('http://127.0.0.1:8000/radar/sources',headers=h,timeout=30); r.raise_for_status(); assert 'items' in r.json(); print('RADAR_SOURCE_API_OK')"
    if ($LASTEXITCODE -ne 0) { throw "RADAR-06 source runtime validation failed." }
}
Write-Host "RADAR-06 validation PASSED. Free collectors and bounded monitoring are operational."
