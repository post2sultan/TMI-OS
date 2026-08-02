param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
$release = Join-Path $Root "releases\P3-MVP-08A"
$backup = Join-Path $release ("backups\" + (Get-Date -Format "yyyyMMdd-HHmmss"))
New-Item -ItemType Directory -Force -Path $backup | Out-Null
$vault = Join-Path $Root "docker\.env.social.vault.json"
if (Test-Path -LiteralPath $vault) { Copy-Item -LiteralPath $vault -Destination (Join-Path $backup "vault.encrypted.backup") }
& (Join-Path $release "validate.ps1") -Root $Root
Write-Host "P3-MVP-08A installation PASSED."
