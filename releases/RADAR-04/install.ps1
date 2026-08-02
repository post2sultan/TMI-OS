param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
& (Join-Path $Root "releases\RADAR-04\validate.ps1") -Root $Root -SourceOnly
Write-Host "RADAR-04 install preflight PASSED."
