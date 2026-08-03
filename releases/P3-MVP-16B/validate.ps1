param([string]$Root = "O:\TMI-OS", [switch]$SourceOnly)
$ErrorActionPreference = "Stop"
$video = Get-Content -LiteralPath (Join-Path $Root "backend\app\services\local_video_service.py") -Raw
if (-not $video.Contains("subtitle_size = 10")) { throw "Mobile-safe subtitle scale is missing." }
if (-not $video.Contains("overlay=W-w-{margin}:H-h-{margin}")) { throw "Protected watermark placement is missing." }
if (-not $SourceOnly) {
    docker exec tmi-production-backend-1 python -c "from app.services.local_video_service import LocalVideoService; import inspect; s=inspect.getsource(LocalVideoService._render); assert 'subtitle_size = 10' in s and 'H-h-{margin}' in s; print('CAPTION_SAFE_AREA_RUNTIME_OK')"
    if ($LASTEXITCODE -ne 0) { throw "Caption safe-area runtime validation failed." }
}
Write-Host "P3-MVP-16B validation PASSED."
