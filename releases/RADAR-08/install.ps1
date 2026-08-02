param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
& (Join-Path $Root "releases\RADAR-08\validate.ps1") -Root $Root -SourceOnly
Write-Host "RADAR-08 install preflight PASSED."
