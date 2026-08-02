param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
$backupRoot = Join-Path $Root "releases\P3-MVP-08A\backups"
$latest = Get-ChildItem $backupRoot -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending | Select-Object -First 1
$backup = if ($latest) { Join-Path $latest.FullName "vault.encrypted.backup" }
if ($backup -and (Test-Path -LiteralPath $backup)) {
    Copy-Item -LiteralPath $backup -Destination (Join-Path $Root "docker\.env.social.vault.json") -Force
    Write-Host "P3-MVP-08A rollback restored the latest encrypted vault backup."
} else {
    Write-Host "P3-MVP-08A rollback: no prior encrypted vault backup was present."
}
