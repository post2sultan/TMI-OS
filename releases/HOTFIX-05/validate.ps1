param([string]$Root = "O:\TMI-OS", [switch]$SourceOnly)
$ErrorActionPreference = "Stop"
$page = Get-Content -LiteralPath (Join-Path $Root "frontend\src\pages\ApprovedPage.tsx") -Raw
if (-not $page.Contains('Campaign #{item.campaign_id}')) { throw "Campaign ID heading is missing." }
$contentIndex = $page.IndexOf('"Regenerate content"')
$voiceIndex = $page.IndexOf('aria-label="Narration voice"')
$videoIndex = $page.IndexOf('"Regenerate video"')
$youtubeIndex = $page.IndexOf('Queue private YouTube upload')
if ($contentIndex -lt 0 -or -not ($contentIndex -lt $voiceIndex -and $voiceIndex -lt $videoIndex -and $videoIndex -lt $youtubeIndex)) {
    throw "Approved workflow controls are not in logical order."
}
if ($page.Contains('Publish to LinkedIn Page (public)')) { throw "Deferred LinkedIn action remains active." }
foreach ($confirmation in @('Publish this Reel publicly on Instagram?', 'Publish this Story publicly on Instagram?', 'Upload this video as a TikTok draft?')) {
    if (-not $page.Contains($confirmation)) { throw "Publishing confirmation missing: $confirmation" }
}
if (-not $SourceOnly) {
    $status = docker inspect tmi-production-frontend-1 --format '{{.State.Health.Status}}'
    if ($LASTEXITCODE -ne 0 -or $status -ne "healthy") { throw "Production frontend is not healthy." }
}
Write-Host "HOTFIX-05 validation PASSED. Campaign identity and workflow order are clear."
