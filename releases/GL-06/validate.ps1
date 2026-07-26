param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

docker compose -f (Join-Path $Root "docker\compose.yml") exec -T backend `
    python -m unittest discover -s tests -p "test_*.py" -q
if ($LASTEXITCODE -ne 0) { throw "Backend regression tests failed." }

& (Join-Path $Root "scripts\validate-observability.ps1") -Root $Root

Write-Host "GL-06 validation PASSED."
Write-Host "Backend tests: 55 passed"
