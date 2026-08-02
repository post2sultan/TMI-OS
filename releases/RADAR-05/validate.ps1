param([string]$Root = "O:\TMI-OS", [switch]$SourceOnly)
$ErrorActionPreference = "Stop"
$planner = Get-Content -LiteralPath (Join-Path $Root "backend\app\services\radar_query_planner.py") -Raw
$router = Get-Content -LiteralPath (Join-Path $Root "backend\app\routers\radar.py") -Raw
if (-not $planner.Contains("DEFAULT_ARABIC_TERMS") -or -not $planner.Contains("DEFAULT_ENGLISH_TERMS")) { throw "Bilingual query planning is incomplete." }
if (-not $planner.Contains("min(max(max_queries, 1), 12)")) { throw "Query expansion ceiling is missing." }
if (-not $planner.Contains("priority_terms")) { throw "Bilingual query priority guard is missing." }
if (-not $router.Contains('/watchlists') -or -not $router.Contains("queries_executed")) { throw "Watchlist API or query telemetry is missing." }
if (-not $SourceOnly) {
    $backend = docker inspect tmi-production-backend-1 --format '{{.State.Health.Status}}'
    if ($backend -ne "healthy") { throw "Production backend is not healthy." }
    docker exec tmi-production-backend-1 python -c "import os,requests; h={'X-TMI-API-Key':os.environ['AUTH_ADMIN_API_KEY'],'X-TMI-Actor':'RADAR-05'}; r=requests.get('http://127.0.0.1:8000/radar/watchlists',headers=h,timeout=30); r.raise_for_status(); assert 'items' in r.json(); print('RADAR_WATCHLIST_API_OK')"
    if ($LASTEXITCODE -ne 0) { throw "RADAR-05 watchlist runtime validation failed." }
}
Write-Host "RADAR-05 validation PASSED. Bilingual watchlists are bounded and operational."
