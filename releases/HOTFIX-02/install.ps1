param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\HOTFIX-02"
$EnvFile = Join-Path $Root "docker\.env.production.local"
$ComposeFile = Join-Path $Root "docker\compose.production.yml"
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$CleanRoot = Join-Path $Root "tmp\hotfix-02-$Stamp"
$Archive = Join-Path $CleanRoot "frontend.zip"
$TagLine = Get-Content -LiteralPath $EnvFile |
    Where-Object { $_ -match "^TMI_RELEASE_TAG=" } |
    Select-Object -First 1
$ReleaseTag = ($TagLine -split "=", 2)[1].Trim()
$Image = "tmi-os-frontend:$ReleaseTag"
$BackupImage = "tmi-os-frontend:pre-hotfix-02-$Stamp"

New-Item -ItemType Directory -Force -Path $CleanRoot | Out-Null
git -C $Root archive --format=zip --output=$Archive HEAD frontend
if ($LASTEXITCODE -ne 0) { throw "Clean frontend archive failed." }
Expand-Archive -LiteralPath $Archive -DestinationPath $CleanRoot

docker image tag $Image $BackupImage
if ($LASTEXITCODE -ne 0) { throw "Frontend image backup failed." }
Set-Content -LiteralPath (Join-Path $Release ".production-backup-image.txt") `
    -Value $BackupImage -Encoding utf8

try {
    docker build -t $Image (Join-Path $CleanRoot "frontend")
    if ($LASTEXITCODE -ne 0) { throw "HOTFIX-02 frontend build failed." }

    docker compose --env-file $EnvFile --project-name tmi-production `
        -f $ComposeFile up -d --no-deps --wait frontend
    if ($LASTEXITCODE -ne 0) { throw "HOTFIX-02 deployment failed." }

    & (Join-Path $Release "validate.ps1") -Root $Root
    Write-Host "HOTFIX-02 installation PASSED."
}
catch {
    docker image tag $BackupImage $Image | Out-Null
    docker compose --env-file $EnvFile --project-name tmi-production `
        -f $ComposeFile up -d --no-deps --wait frontend | Out-Null
    throw
}
