param([string]$Root="O:\TMI-OS")
$w=Get-Content (Join-Path $Root "tools\social-publishing\instagram-worker.ps1") -Raw
if($w -notmatch 'STORIES' -or $w -notmatch 'instagram-story'){throw "Instagram Story workflow is missing."}; if($w -notmatch '\-t 59'){throw "Story duration guard is missing."}; if($w -notmatch 'Stop-Process'){throw "Tunnel shutdown guard is missing."}
Write-Host "P3-MVP-11 validation PASSED."
