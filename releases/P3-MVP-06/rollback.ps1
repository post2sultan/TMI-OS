param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
$backupRoot = Join-Path $Root "releases\P3-MVP-06\backups"
$latest = Get-ChildItem $backupRoot -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending | Select-Object -First 1
foreach ($name in @("TERMS_OF_SERVICE.md", "PRIVACY_POLICY.md")) {
    $target = Join-Path $Root "docs\$name"
    $backup = if ($latest) { Join-Path $latest.FullName $name }
    if ($backup -and (Test-Path -LiteralPath $backup)) {
        Copy-Item -LiteralPath $backup -Destination $target -Force
    } elseif (Test-Path -LiteralPath $target) {
        Remove-Item -LiteralPath $target -Force
    }
}
Write-Host "P3-MVP-06 rollback PASSED."
