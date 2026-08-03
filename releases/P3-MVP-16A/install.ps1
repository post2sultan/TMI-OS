param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
& (Join-Path $Root "releases\P3-MVP-16A\validate.ps1") -Root $Root -SourceOnly
Write-Host "P3-MVP-16A install preflight PASSED."
