param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
& (Join-Path $Root "scripts\validate-operations.ps1") -Root $Root
Write-Host "GL-07 validation PASSED."
