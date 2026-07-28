param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\P3-MVP-01"
$EnvFile = Join-Path $Root "docker\.env.production.local"
$ComposeFile = Join-Path $Root "docker\compose.production.yml"
$BackendBackup = (Get-Content (Join-Path $Release ".production-backend-image.txt") -Raw).Trim()
$FrontendBackup = (Get-Content (Join-Path $Release ".production-frontend-image.txt") -Raw).Trim()
$TagLine = Get-Content -LiteralPath $EnvFile |
    Where-Object { $_ -match "^TMI_RELEASE_TAG=" } |
    Select-Object -First 1
$ReleaseTag = ($TagLine -split "=", 2)[1].Trim()

docker compose --env-file $EnvFile --project-name tmi-production `
    -f $ComposeFile run --rm backend alembic downgrade d6a9c2e4f7b1
if ($LASTEXITCODE -ne 0) { throw "Database rollback failed." }
docker image tag $BackendBackup "tmi-os-backend:$ReleaseTag"
docker image tag $FrontendBackup "tmi-os-frontend:$ReleaseTag"
docker compose --env-file $EnvFile --project-name tmi-production `
    -f $ComposeFile up -d --no-deps --wait backend frontend
if ($LASTEXITCODE -ne 0) { throw "Service rollback failed." }
Write-Host "P3-MVP-01 rollback PASSED."
