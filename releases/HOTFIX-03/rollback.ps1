param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\HOTFIX-03"
$EnvFile = Join-Path $Root "docker\.env.production.local"
$ComposeFile = Join-Path $Root "docker\compose.production.yml"
$BackupFile = Join-Path $Release ".production-backup-image.txt"
$TagLine = Get-Content -LiteralPath $EnvFile |
    Where-Object { $_ -match "^TMI_RELEASE_TAG=" } |
    Select-Object -First 1
$ReleaseTag = ($TagLine -split "=", 2)[1].Trim()
$Image = "tmi-os-backend:$ReleaseTag"
$BackupImage = (Get-Content -LiteralPath $BackupFile -Raw).Trim()

docker image tag $BackupImage $Image
if ($LASTEXITCODE -ne 0) { throw "Backend image restore failed." }
docker compose --env-file $EnvFile --project-name tmi-production `
    -f $ComposeFile up -d --no-deps --wait backend
if ($LASTEXITCODE -ne 0) { throw "Backend rollback deployment failed." }
Write-Host "HOTFIX-03 rollback PASSED."
