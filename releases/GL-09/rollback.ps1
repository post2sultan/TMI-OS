param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\GL-09"
$EnvFile = Join-Path $Root "docker\.env.production.local"
$ComposeFile = Join-Path $Root "docker\compose.production.yml"
$BackendBackup = (Get-Content (Join-Path $Release ".production-backend-image.txt") -Raw).Trim()
$FrontendBackup = (Get-Content (Join-Path $Release ".production-frontend-image.txt") -Raw).Trim()
$TagLine = Get-Content -LiteralPath $EnvFile |
    Where-Object { $_ -match "^TMI_RELEASE_TAG=" } |
    Select-Object -First 1
$ReleaseTag = ($TagLine -split "=", 2)[1].Trim()

docker compose --env-file $EnvFile --project-name tmi-production `
    -f $ComposeFile run --rm backend alembic downgrade c5f8a1d3e6b9
if ($LASTEXITCODE -ne 0) { throw "Database rollback failed." }
docker image tag $BackendBackup "tmi-os-backend:$ReleaseTag"
docker image tag $FrontendBackup "tmi-os-frontend:$ReleaseTag"
docker compose --env-file $EnvFile --project-name tmi-production `
    -f $ComposeFile up -d --no-deps --wait backend frontend
if ($LASTEXITCODE -ne 0) { throw "Service rollback failed." }
Write-Host "GL-09 rollback PASSED."
