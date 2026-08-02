param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
& (Join-Path $Root "releases\RADAR-07\validate.ps1") -Root $Root -SourceOnly
Write-Host "RADAR-07 install preflight PASSED."
