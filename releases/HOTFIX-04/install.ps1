param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
& (Join-Path $Root "releases\HOTFIX-04\validate.ps1") -Root $Root -SourceOnly
Write-Host "HOTFIX-04 install preflight PASSED."
