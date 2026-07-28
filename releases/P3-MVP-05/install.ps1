param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
$Release = Join-Path $Root "releases\P3-MVP-05"
$Backup = Join-Path $Release ("backups\" + (Get-Date -Format "yyyyMMdd-HHmmss"))
New-Item -ItemType Directory -Force -Path $Backup | Out-Null
$Vault = Join-Path $Root "docker\.env.social.vault.json"
if (Test-Path $Vault) { Copy-Item $Vault (Join-Path $Backup "vault.encrypted.backup") }
& (Join-Path $Release "validate.ps1") -Root $Root
Write-Host "P3-MVP-05 installation PASSED."
