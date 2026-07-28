param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
$Release = Join-Path $Root "releases\P3-MVP-04"
$EnvFile = Join-Path $Root "docker\.env.production.local"
$ComposeFile = Join-Path $Root "docker\compose.production.yml"
$TagLine = Get-Content $EnvFile | Where-Object { $_ -match "^TMI_RELEASE_TAG=" } | Select-Object -First 1
$Tag = ($TagLine -split "=",2)[1].Trim()
docker image tag ((Get-Content (Join-Path $Release ".production-backend-image.txt") -Raw).Trim()) "tmi-os-backend:$Tag"
docker image tag ((Get-Content (Join-Path $Release ".production-frontend-image.txt") -Raw).Trim()) "tmi-os-frontend:$Tag"
docker compose --env-file $EnvFile --project-name tmi-production -f $ComposeFile up -d --no-deps --wait backend frontend
if ($LASTEXITCODE -ne 0) { throw "Rollback failed." }
Write-Host "P3-MVP-04 rollback PASSED."
