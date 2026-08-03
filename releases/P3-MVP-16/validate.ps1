param([string]$Root = "O:\TMI-OS", [switch]$SourceOnly)
$ErrorActionPreference = "Stop"
$video = Get-Content -LiteralPath (Join-Path $Root "backend\app\services\local_video_service.py") -Raw
$stock = Get-Content -LiteralPath (Join-Path $Root "backend\app\services\stock_media_service.py") -Raw
if (-not $video.Contains("tmi-logo.png") -or -not $video.Contains("video-landscape.mp4")) { throw "Mandatory watermark or dual-format render is missing." }
if (-not $stock.Contains("STOCK_MEDIA_MAX_SEARCHES") -or -not $stock.Contains("media-manifest.json")) { throw "Stock API ceiling or provenance is missing." }
if (-not (Test-Path -LiteralPath (Join-Path $Root "backend\assets\brand\tmi-logo.png"))) { throw "Brand logo asset is missing." }
if (-not $SourceOnly) {
    $backend = docker inspect tmi-production-backend-1 --format '{{.State.Health.Status}}'
    $frontend = docker inspect tmi-production-frontend-1 --format '{{.State.Health.Status}}'
    if ($backend -ne "healthy" -or $frontend -ne "healthy") { throw "Production application is not healthy." }
    docker exec tmi-production-backend-1 python -c "from app.core.settings import settings; assert settings.STOCK_MEDIA_MAX_SEARCHES <= 3; assert settings.STOCK_MEDIA_MAX_ASSETS <= 6; import pathlib; assert pathlib.Path('/app/assets/brand/tmi-logo.png').is_file(); print('CREATIVE_MEDIA_RUNTIME_OK')"
    if ($LASTEXITCODE -ne 0) { throw "Creative media runtime validation failed." }
}
Write-Host "P3-MVP-16 validation PASSED."
