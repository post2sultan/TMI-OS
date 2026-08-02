param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
& (Join-Path $Root "releases\P3-MVP-08\validate.ps1") -Root $Root
Write-Host "P3-MVP-08A compatibility validation PASSED. Current LinkedIn OAuth helper is valid."
