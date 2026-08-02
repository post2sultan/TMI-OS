param([string]$Root="O:\TMI-OS")
$ErrorActionPreference="Stop";& (Join-Path $Root "tools\social-credentials\verify.ps1") -Root $Root -Platform LinkedIn
Write-Host "P3-MVP-13 install preflight PASSED."
