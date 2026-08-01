param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
$backupRoot = Join-Path $Root "releases\P3-MVP-05A\backups"
$latest = Get-ChildItem $backupRoot -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending | Select-Object -First 1
$backupVault = if ($latest) { Join-Path $latest.FullName "vault.encrypted.backup" }
if ($backupVault -and (Test-Path -LiteralPath $backupVault)) {
    Copy-Item -LiteralPath $backupVault -Destination (Join-Path $Root "docker\.env.social.vault.json") -Force
    Write-Host "P3-MVP-05A rollback restored the latest encrypted vault backup."
} else {
    Write-Host "P3-MVP-05A rollback: no prior vault existed; no data changed."
}
