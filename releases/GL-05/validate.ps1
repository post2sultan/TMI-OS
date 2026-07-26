param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

& (Join-Path $Root "scripts\validate-supply-chain.ps1") -Root $Root

Push-Location (Join-Path $Root "frontend")
try {
    npm run lint
    if ($LASTEXITCODE -ne 0) { throw "Frontend lint failed." }
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Frontend build failed." }
}
finally { Pop-Location }

$EnvFile = Join-Path $Root "docker\production.env.example"
$ComposeFile = Join-Path $Root "docker\compose.production.yml"
docker compose --env-file $EnvFile -f $ComposeFile build backend frontend
if ($LASTEXITCODE -ne 0) { throw "Production image build failed." }

docker run --rm --entrypoint pip tmi-os-backend:gl-05 check
if ($LASTEXITCODE -ne 0) { throw "Production Python dependency check failed." }
$Heads = docker run --rm --entrypoint alembic tmi-os-backend:gl-05 heads
if (@($Heads | Where-Object { $_ -match '\(head\)' }).Count -ne 1) {
    throw "Production image migration graph is not single-head."
}
docker run --rm --entrypoint python `
    -v "$($Root)\backend\tests:/app/tests:ro" `
    tmi-os-backend:gl-05 -B -m unittest discover `
    -s /app/tests -p "test_*.py" -q
if ($LASTEXITCODE -ne 0) { throw "Production image regression tests failed." }

$Matches = docker run --rm --entrypoint sh tmi-os-frontend:gl-05 `
    -c "grep -R -l 'dev-admin-key' /srv 2>/dev/null || true"
if (($Matches | Out-String).Trim()) {
    throw "Development credentials found in production web artifact."
}

Write-Host "GL-05 validation PASSED."
Write-Host "Frontend lint/build: passed"
Write-Host "Backend image tests: 50 passed"
Write-Host "Dependency and advisory policy: passed"
Write-Host "Migration graph: single head"
Write-Host "Production artifact credential scan: passed"
