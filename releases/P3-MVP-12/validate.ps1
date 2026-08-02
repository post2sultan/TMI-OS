param([string]$Root="O:\TMI-OS")
$ErrorActionPreference="Stop"
$worker=Get-Content (Join-Path $Root "tools\social-publishing\tiktok-worker.ps1") -Raw
if($worker -notmatch '/v2/post/publish/inbox/video/init/'){throw "TikTok draft endpoint is missing."}
if($worker -match '/v2/post/publish/video/init/'){throw "TikTok direct-post endpoint is forbidden."}
if($worker -notmatch 'video.upload' -and (Get-Content (Join-Path $Root "tools\social-credentials\tiktok-authorize.ps1") -Raw) -notmatch 'video.upload'){throw "TikTok upload scope is missing."}
if($worker -notmatch 'Content-Range' -or $worker -notmatch 'FILE_UPLOAD'){throw "TikTok file transfer guard is missing."}
if($worker -notmatch 'refresh_token'){throw "TikTok token refresh guard is missing."}
Write-Host "P3-MVP-12 validation PASSED. Draft-only upload; no direct public posting."
