param(
    [string]$Root = "O:\TMI-OS",
    [switch]$SkipStaging
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Required = @(
    "docker\compose.staging.yml",
    "docs\OPERATIONS.md",
    "docs\INCIDENT_RESPONSE.md",
    "docs\CREDENTIAL_ROTATION.md",
    "scripts\deploy-release.ps1",
    "scripts\rollback-release.ps1",
    "scripts\new-credential-bundle.ps1",
    "scripts\validate-staging.ps1"
)
foreach ($RelativePath in $Required) {
    if (-not (Test-Path (Join-Path $Root $RelativePath))) {
        throw "GL-07 artifact missing: $RelativePath"
    }
}

$Deploy = Get-Content (Join-Path $Root "scripts\deploy-release.ps1") -Raw
foreach ($Contract in @(
    "ApproveProduction", "backup-data.ps1", "--wait", "REPLACE_WITH_"
)) {
    if ($Deploy -notmatch [regex]::Escape($Contract)) {
        throw "Deployment safety contract missing: $Contract"
    }
}
$Rollback = Get-Content (Join-Path $Root "scripts\rollback-release.ps1") -Raw
foreach ($Contract in @("PreviousReleaseTag", "image inspect", "--no-build", "--wait")) {
    if ($Rollback -notmatch [regex]::Escape($Contract)) {
        throw "Rollback safety contract missing: $Contract"
    }
}

docker compose -f (Join-Path $Root "docker\compose.yml") exec -T backend `
    python -m unittest discover -s tests -p "test_*.py" -q
if ($LASTEXITCODE -ne 0) { throw "Backend regression tests failed." }

if (-not $SkipStaging) {
    & (Join-Path $Root "scripts\validate-staging.ps1") -Root $Root
}
Write-Host "GL-07 operations validation PASSED."
