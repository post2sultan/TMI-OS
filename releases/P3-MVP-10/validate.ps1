param([string]$Root="O:\TMI-OS")
$ErrorActionPreference="Stop"; $w=Get-Content (Join-Path $Root "tools\social-publishing\instagram-worker.ps1") -Raw
if($w -notmatch 'trycloudflare'){throw "Temporary tunnel guard is missing."}; if($w -notmatch 'media_publish'){throw "Instagram publish step is missing."}; if($w -notmatch 'Stop-Process'){throw "Tunnel shutdown guard is missing."}
Write-Host "P3-MVP-10 validation PASSED."
