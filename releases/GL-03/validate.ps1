param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$BaseUrl = "http://127.0.0.1:8000"
$Health = Invoke-RestMethod "$BaseUrl/health" -TimeoutSec 15
$Ready = Invoke-RestMethod "$BaseUrl/ready" -TimeoutSec 15
if ($Health.status -ne "healthy" -or $Ready.status -ne "ready") {
    throw "Development stack health validation failed."
}

Push-Location (Join-Path $Root "frontend")
try {
    npm run lint
    if ($LASTEXITCODE -ne 0) { throw "Frontend lint failed." }
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Frontend build failed." }
}
finally {
    Pop-Location
}

& (Join-Path $Root "scripts\validate-production-web.ps1") -Root $Root

$ComposeFile = Join-Path $Root "docker\compose.yml"
docker compose -f $ComposeFile exec -T backend python -B -m unittest discover -s /app/tests -p "test_*.py" -q
if ($LASTEXITCODE -ne 0) { throw "Backend regression tests failed." }

$Migration = docker compose -f $ComposeFile exec -T backend alembic current
if (($Migration | Out-String) -notmatch "c5f8a1d3e6b9") {
    throw "Expected migration head is not active."
}

Write-Host "GL-03 validation PASSED."
Write-Host "Authenticated HTTPS gateway contract: passed"
Write-Host "Same-origin API proxy: passed"
Write-Host "Production browser secrets: none"
Write-Host "Frontend lint and build: passed"
Write-Host "Backend regression tests: passed"
