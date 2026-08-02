param([string]$Root = "O:\TMI-OS", [switch]$SourceOnly)
$ErrorActionPreference = "Stop"
$intelligence = Get-Content -LiteralPath (Join-Path $Root "backend\app\services\radar_cluster_intelligence.py") -Raw
$signalService = Get-Content -LiteralPath (Join-Path $Root "backend\app\services\radar_signal_service.py") -Raw
$router = Get-Content -LiteralPath (Join-Path $Root "backend\app\routers\radar.py") -Raw
if (-not $intelligence.Contains("title_similarity") -or -not $intelligence.Contains("extract_known_entities") -or -not $intelligence.Contains("score_cluster")) { throw "Radar local intelligence functions are incomplete." }
if (-not $signalService.Contains("similarity_threshold = 0.62") -or -not $signalService.Contains("candidate_scan_limit = 250")) { throw "Local clustering safety bounds are missing." }
if (-not $router.Contains('sort == "trend"') -or -not $router.Contains("min_confidence")) { throw "Ranked candidate API is incomplete." }
if (-not $SourceOnly) {
    $backend = docker inspect tmi-production-backend-1 --format '{{.State.Health.Status}}'
    if ($backend -ne "healthy") { throw "Production backend is not healthy." }
    docker exec tmi-production-backend-1 python -c "import os,requests; h={'X-TMI-API-Key':os.environ['AUTH_ADMIN_API_KEY'],'X-TMI-Actor':'RADAR-07'}; r=requests.get('http://127.0.0.1:8000/radar/clusters?sort=trend&limit=5',headers=h,timeout=30); r.raise_for_status(); d=r.json(); assert 'items' in d; assert all('trend_score' in x and 'score_rationale' in x for x in d['items']); print('RADAR_INTELLIGENCE_API_OK')"
    if ($LASTEXITCODE -ne 0) { throw "RADAR-07 runtime validation failed." }
}
Write-Host "RADAR-07 validation PASSED. Local entity, clustering, confidence, and trend intelligence are operational."
