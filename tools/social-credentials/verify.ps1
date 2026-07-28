param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
Import-Module (Join-Path $PSScriptRoot "SocialCredentialVault.psm1") -Force
Test-TmiSocialVault -Path (Join-Path $Root "docker\.env.social.vault.json") | Out-Null
Write-Host "Credential vault structure and Windows decryption PASSED."
Write-Host "No credential values were displayed."
