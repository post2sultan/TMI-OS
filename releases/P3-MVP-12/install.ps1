param([string]$Root="O:\TMI-OS")
$ErrorActionPreference="Stop"
& (Join-Path $Root "tools\social-credentials\verify.ps1") -Root $Root -Platform TikTok
Write-Host "P3-MVP-12 install preflight PASSED."
