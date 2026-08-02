param([string]$Root="O:\TMI-OS")
$ErrorActionPreference="Stop";$w=Get-Content (Join-Path $Root "tools\social-publishing\linkedin-worker.ps1") -Raw
if($w -notmatch 'rest/videos\?action=initializeUpload' -or $w -notmatch 'action=finalizeUpload'){throw "LinkedIn video upload flow is incomplete."}
if($w -notmatch 'rest/posts' -or $w -notmatch 'visibility="PUBLIC"'){throw "LinkedIn public post flow is incomplete."}
if($w -notmatch 'LinkedIn-Version.*202607' -or $w -notmatch 'X-Restli-Protocol-Version'){throw "LinkedIn version headers are missing."}
if($w -notmatch 'linkedin\\post.mp4'){throw "LinkedIn square-video selection is missing."}
if($w -notmatch 'urn:li:organization:\*'){throw "LinkedIn organization-only safety guard is missing."}
Write-Host "P3-MVP-13 validation PASSED."
