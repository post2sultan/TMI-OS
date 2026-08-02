param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
$backups = Get-ChildItem -LiteralPath (Join-Path $Root "releases\P3-MVP-14\backups") -Directory | Sort-Object Name -Descending
if (-not $backups) { throw "No P3-MVP-14 backup exists." }
Copy-Item -Force -LiteralPath (Join-Path $backups[0].FullName "BACKLOG.md") -Destination (Join-Path $Root "docs\BACKLOG.md")
Write-Host "P3-MVP-14 rollback PASSED."
