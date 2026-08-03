param([string]$Root = "O:\TMI-OS", [switch]$SourceOnly)
$ErrorActionPreference = "Stop"
$video = Get-Content -LiteralPath (Join-Path $Root "backend\app\services\local_video_service.py") -Raw
if (-not $video.Contains("OutlineColour=&H006B4C03")) { throw "TMI navy subtitle mapping is missing." }
if (-not $video.Contains("[branded]subtitles=")) { throw "Caption-over-watermark ordering is missing." }
if (-not $SourceOnly) {
    docker exec tmi-production-backend-1 python -c "from app.services.local_video_service import LocalVideoService; import inspect; s=inspect.getsource(LocalVideoService._render); assert 'OutlineColour=&H006B4C03' in s and '[branded]subtitles=' in s; print('OVERLAY_POLISH_RUNTIME_OK')"
    if ($LASTEXITCODE -ne 0) { throw "Overlay runtime validation failed." }
}
Write-Host "P3-MVP-16A validation PASSED."
