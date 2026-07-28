param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\HOTFIX-03"
$EnvFile = Join-Path $Root "docker\.env.production.local"
$ComposeFile = Join-Path $Root "docker\compose.production.yml"
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$CleanRoot = Join-Path $Root "tmp\hotfix-03-$Stamp"
$Archive = Join-Path $CleanRoot "backend.zip"
$TagLine = Get-Content -LiteralPath $EnvFile |
    Where-Object { $_ -match "^TMI_RELEASE_TAG=" } |
    Select-Object -First 1
$ReleaseTag = ($TagLine -split "=", 2)[1].Trim()
$Image = "tmi-os-backend:$ReleaseTag"
$BackupImage = "tmi-os-backend:pre-hotfix-03-$Stamp"

New-Item -ItemType Directory -Force -Path $CleanRoot | Out-Null
git -C $Root archive --format=zip --output=$Archive HEAD backend
if ($LASTEXITCODE -ne 0) { throw "Clean backend archive failed." }
Expand-Archive -LiteralPath $Archive -DestinationPath $CleanRoot

docker image tag $Image $BackupImage
if ($LASTEXITCODE -ne 0) { throw "Backend image backup failed." }
Set-Content -LiteralPath (Join-Path $Release ".production-backup-image.txt") `
    -Value $BackupImage -Encoding utf8

try {
    docker build -t $Image (Join-Path $CleanRoot "backend")
    if ($LASTEXITCODE -ne 0) { throw "HOTFIX-03 backend build failed." }

    docker compose --env-file $EnvFile --project-name tmi-production `
        -f $ComposeFile up -d --no-deps --wait backend
    if ($LASTEXITCODE -ne 0) { throw "HOTFIX-03 deployment failed." }

    & (Join-Path $Release "validate.ps1") -Root $Root
    Write-Host "HOTFIX-03 installation PASSED."
}
catch {
    docker image tag $BackupImage $Image | Out-Null
    docker compose --env-file $EnvFile --project-name tmi-production `
        -f $ComposeFile up -d --no-deps --wait backend | Out-Null
    throw
}
