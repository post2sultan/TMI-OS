param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
& (Join-Path $Root "releases\P3-MVP-08\validate.ps1") -Root $Root
Write-Host "P3-MVP-08A validation PASSED. Native PKCE endpoint and secret-free token exchange confirmed."
