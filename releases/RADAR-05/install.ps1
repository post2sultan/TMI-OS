param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
& (Join-Path $Root "releases\RADAR-05\validate.ps1") -Root $Root -SourceOnly
Write-Host "RADAR-05 install preflight PASSED."
