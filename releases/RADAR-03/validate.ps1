param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Page = Join-Path $Root "frontend\src\pages\CampaignRadarPage.tsx"
$Source = Get-Content -LiteralPath $Page -Raw

if ($Source -notmatch 'toUpperCase\(\)') {
    throw "Provider status normalization is missing."
}
if ($Source -notmatch 'Operational') {
    throw "Operational provider label is missing."
}
if ($Source -notmatch 'credits_used === 0') {
    throw "Zero-credit provider display is missing."
}
if ($Source -match 'run\.status === "success"') {
    throw "Case-sensitive legacy status check remains."
}

Push-Location (Join-Path $Root "frontend")
try {
    npm run build
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend production build failed."
    }
    npm run lint
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend lint failed."
    }
}
finally {
    Pop-Location
}

$ContainerHealth = docker inspect tmi-production-frontend-1 `
    --format "{{.State.Health.Status}}"
if ($LASTEXITCODE -ne 0 -or ($ContainerHealth | Out-String).Trim() -ne "healthy") {
    throw "Production frontend container is not healthy."
}

Write-Host ""
Write-Host "RADAR-03 validation PASSED."
Write-Host "Provider status normalization: enabled"
Write-Host "Zero-credit display: enabled"
Write-Host "Frontend build and lint: passed"
Write-Host "Runtime container health: healthy"
