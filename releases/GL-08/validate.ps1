param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
& (Join-Path $Root "scripts\validate-launch-rehearsal.ps1") -Root $Root
Write-Host "GL-08 validation PASSED."
