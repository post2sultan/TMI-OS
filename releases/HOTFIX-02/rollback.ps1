param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\HOTFIX-02"
$EnvFile = Join-Path $Root "docker\.env.production.local"
$ComposeFile = Join-Path $Root "docker\compose.production.yml"
$BackupFile = Join-Path $Release ".production-backup-image.txt"
$TagLine = Get-Content -LiteralPath $EnvFile |
    Where-Object { $_ -match "^TMI_RELEASE_TAG=" } |
    Select-Object -First 1
$ReleaseTag = ($TagLine -split "=", 2)[1].Trim()
$Image = "tmi-os-frontend:$ReleaseTag"
$BackupImage = (Get-Content -LiteralPath $BackupFile -Raw).Trim()

docker image tag $BackupImage $Image
if ($LASTEXITCODE -ne 0) { throw "Frontend image restore failed." }
docker compose --env-file $EnvFile --project-name tmi-production `
    -f $ComposeFile up -d --no-deps --wait frontend
if ($LASTEXITCODE -ne 0) { throw "Frontend rollback deployment failed." }
Write-Host "HOTFIX-02 rollback PASSED."
