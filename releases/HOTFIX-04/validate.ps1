param([string]$Root = "O:\TMI-OS", [switch]$SourceOnly)
$ErrorActionPreference = "Stop"
$page = Get-Content -LiteralPath (Join-Path $Root "frontend\src\pages\ApprovedPage.tsx") -Raw
foreach ($required in @("grid gap-4", "min-w-0 overflow-hidden", "flex min-w-0 flex-wrap gap-2", "w-full max-w-sm")) {
    if (-not $page.Contains($required)) { throw "Responsive layout guard missing: $required" }
}
if ($page.Contains('grid gap-4 lg:grid-cols-2')) { throw "Approved cards still use the overlapping two-column layout." }
if (-not $SourceOnly) {
    $status = docker inspect tmi-production-frontend-1 --format '{{.State.Health.Status}}'
    if ($LASTEXITCODE -ne 0 -or $status -ne "healthy") { throw "Production frontend is not healthy." }
}
Write-Host "HOTFIX-04 validation PASSED. Approved layout is responsive."
