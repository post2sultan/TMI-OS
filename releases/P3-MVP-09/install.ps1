param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
& (Join-Path $Root "tools\social-credentials\verify.ps1") -Root $Root -Platform YouTube
Write-Host "P3-MVP-09 install preflight PASSED. Deploy through scripts/deploy-release.ps1."
