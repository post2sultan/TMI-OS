param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
& (Join-Path $Root "releases\RADAR-06\validate.ps1") -Root $Root -SourceOnly
Write-Host "RADAR-06 install preflight PASSED."
