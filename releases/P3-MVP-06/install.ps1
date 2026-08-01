param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
$release = Join-Path $Root "releases\P3-MVP-06"
$backup = Join-Path $release ("backups\" + (Get-Date -Format "yyyyMMdd-HHmmss"))
New-Item -ItemType Directory -Force -Path $backup | Out-Null
foreach ($name in @("TERMS_OF_SERVICE.md", "PRIVACY_POLICY.md")) {
    $source = Join-Path $Root "docs\$name"
    if (Test-Path -LiteralPath $source) { Copy-Item -LiteralPath $source -Destination (Join-Path $backup $name) }
}
& (Join-Path $release "validate.ps1") -Root $Root
Write-Host "P3-MVP-06 installation PASSED."
