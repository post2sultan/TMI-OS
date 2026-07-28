param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
$Backups = Get-ChildItem (Join-Path $Root "releases\P3-MVP-05\backups") -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending
$Latest = $Backups | Select-Object -First 1
if ($Latest -and (Test-Path (Join-Path $Latest.FullName "vault.encrypted.backup"))) {
    Copy-Item (Join-Path $Latest.FullName "vault.encrypted.backup") (Join-Path $Root "docker\.env.social.vault.json") -Force
}
Write-Host "P3-MVP-05 rollback PASSED."
