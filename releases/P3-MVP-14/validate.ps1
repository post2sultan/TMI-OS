param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
$backlog = Get-Content -LiteralPath (Join-Path $Root "docs\BACKLOG.md") -Raw
$worker = Get-Content -LiteralPath (Join-Path $Root "tools\social-publishing\linkedin-worker.ps1") -Raw
if ($backlog -notmatch "LinkedIn Page Publishing") { throw "LinkedIn deferral is not recorded." }
if ($backlog -notmatch "P3-MVP-14 Final Launch Acceptance") { throw "Final launch acceptance is not recorded as next." }
if ($backlog -notmatch "YouTube video and Shorts" -or $backlog -notmatch "Instagram Reel" -or $backlog -notmatch "TikTok") { throw "Supported launch channels are incomplete." }
if ($worker -notmatch 'urn:li:organization:\*') { throw "LinkedIn organization-only safety guard is missing." }
Write-Host "P3-MVP-14 validation PASSED. Launch scope locked; LinkedIn safely deferred."
