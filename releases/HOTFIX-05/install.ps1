param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
& (Join-Path $Root "releases\HOTFIX-05\validate.ps1") -Root $Root -SourceOnly
Write-Host "HOTFIX-05 install preflight PASSED."
