param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
$release = Join-Path $Root "releases\P3-MVP-14"
$target = Join-Path $Root "docs\BACKLOG.md"
$patch = Join-Path $release "patch\docs\BACKLOG.md"
$backup = Join-Path $release ("backups\" + (Get-Date -Format "yyyyMMdd-HHmmss"))
if (-not (Test-Path -LiteralPath $patch)) { throw "P3-MVP-14 patch is missing." }
New-Item -ItemType Directory -Force -Path $backup | Out-Null
Copy-Item -Force -LiteralPath $target -Destination (Join-Path $backup "BACKLOG.md")
Copy-Item -Force -LiteralPath $patch -Destination $target
& (Join-Path $Root "releases\P3-MVP-14\validate.ps1") -Root $Root
Write-Host "P3-MVP-14 installation PASSED. Documentation-only; no runtime restart required."
