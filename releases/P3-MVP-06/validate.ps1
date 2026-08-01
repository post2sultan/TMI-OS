param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
$terms = Join-Path $Root "docs\TERMS_OF_SERVICE.md"
$privacy = Join-Path $Root "docs\PRIVACY_POLICY.md"
foreach ($path in @($terms, $privacy)) {
    if (-not (Test-Path -LiteralPath $path)) { throw "Required public document missing: $path" }
    if ((Get-Item -LiteralPath $path).Length -lt 500) { throw "Public document is unexpectedly incomplete: $path" }
}
$termsText = Get-Content -LiteralPath $terms -Raw
$privacyText = Get-Content -LiteralPath $privacy -Raw
foreach ($heading in @("Authorized use", "Platform connections", "Local operation and credentials")) {
    if ($termsText -notmatch [regex]::Escape($heading)) { throw "Terms section missing: $heading" }
}
foreach ($heading in @("Information processed", "Storage and security", "Retention and deletion")) {
    if ($privacyText -notmatch [regex]::Escape($heading)) { throw "Privacy section missing: $heading" }
}
if ($privacyText -notmatch "not sold") { throw "Privacy policy must state the data-sale position." }
Write-Host "P3-MVP-06 validation PASSED. Public Terms and Privacy documents are complete."
Write-Host "No external service or paid API used. Paid credits: 0"
