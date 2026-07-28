param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\HOTFIX-01"
$BackupFile = Join-Path $Release ".production-backup-image.txt"
$EnvFile = Join-Path $Root "docker\.env.production.local"
$ComposeFile = Join-Path $Root "docker\compose.production.yml"

if (-not (Test-Path $BackupFile)) {
    throw "HOTFIX-01 backup image reference is missing."
}
$BackupImage = (Get-Content -LiteralPath $BackupFile -Raw).Trim()
$TagLine = Get-Content -LiteralPath $EnvFile |
    Where-Object { $_ -match "^TMI_RELEASE_TAG=" } |
    Select-Object -First 1
$ReleaseTag = ($TagLine -split "=", 2)[1].Trim()
$Image = "tmi-os-backend:$ReleaseTag"

docker image tag $BackupImage $Image
if ($LASTEXITCODE -ne 0) { throw "Could not restore backend image." }
docker compose --env-file $EnvFile --project-name tmi-production `
    -f $ComposeFile up -d --no-deps --wait backend
if ($LASTEXITCODE -ne 0) { throw "Backend rollback deployment failed." }

Write-Host "HOTFIX-01 rollback PASSED."
