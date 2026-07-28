param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$Release = Join-Path $Root "releases\P3-MVP-02A"
$EnvFile = Join-Path $Root "docker\.env.production.local"
$ComposeFile = Join-Path $Root "docker\compose.production.yml"
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$CleanRoot = Join-Path $Root "tmp\p3-mvp-02a-$Stamp"
$BackupDir = Join-Path $Release "backups\$Stamp"
$Archive = Join-Path $CleanRoot "source.zip"
$TagLine = Get-Content -LiteralPath $EnvFile | Where-Object { $_ -match "^TMI_RELEASE_TAG=" } | Select-Object -First 1
$ReleaseTag = ($TagLine -split "=", 2)[1].Trim()
$BackendImage = "tmi-os-backend:$ReleaseTag"
$FrontendImage = "tmi-os-frontend:$ReleaseTag"
$BackendBackup = "tmi-os-backend:pre-p3-mvp-02a-$Stamp"
$FrontendBackup = "tmi-os-frontend:pre-p3-mvp-02a-$Stamp"

New-Item -ItemType Directory -Force -Path $CleanRoot, $BackupDir | Out-Null
git -C $Root archive --format=zip "--output=$Archive" HEAD backend frontend
if ($LASTEXITCODE -ne 0) { throw "Clean source archive failed." }
Expand-Archive -LiteralPath $Archive -DestinationPath $CleanRoot
docker image tag $BackendImage $BackendBackup
docker image tag $FrontendImage $FrontendBackup
if ($LASTEXITCODE -ne 0) { throw "Image backup failed." }
Set-Content (Join-Path $Release ".production-backend-image.txt") $BackendBackup -Encoding utf8
Set-Content (Join-Path $Release ".production-frontend-image.txt") $FrontendBackup -Encoding utf8

$DbBackupName = "p3-mvp-02a-$Stamp.sql"
docker exec tmi-production-postgres-1 sh -c "pg_dump -U `"`$POSTGRES_USER`" `"`$POSTGRES_DB`" > /tmp/$DbBackupName"
if ($LASTEXITCODE -ne 0) { throw "Database backup failed." }
docker cp "tmi-production-postgres-1:/tmp/$DbBackupName" (Join-Path $BackupDir $DbBackupName)
if ($LASTEXITCODE -ne 0) { throw "Database backup copy failed." }

try {
    docker build -t $BackendImage (Join-Path $CleanRoot "backend")
    if ($LASTEXITCODE -ne 0) { throw "Backend build failed." }
    docker build -t $FrontendImage (Join-Path $CleanRoot "frontend")
    if ($LASTEXITCODE -ne 0) { throw "Frontend build failed." }
    docker compose --env-file $EnvFile --project-name tmi-production -f $ComposeFile run --rm backend alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw "Database migration failed." }
    docker compose --env-file $EnvFile --project-name tmi-production -f $ComposeFile up -d --no-deps --wait backend frontend
    if ($LASTEXITCODE -ne 0) { throw "Production deployment failed." }
    & (Join-Path $Release "validate.ps1") -Root $Root
    Write-Host "P3-MVP-02A installation PASSED."
}
catch {
    docker compose --env-file $EnvFile --project-name tmi-production -f $ComposeFile run --rm backend alembic downgrade f8c2e4a6b0d3 | Out-Null
    docker image tag $BackendBackup $BackendImage | Out-Null
    docker image tag $FrontendBackup $FrontendImage | Out-Null
    docker compose --env-file $EnvFile --project-name tmi-production -f $ComposeFile up -d --no-deps --wait backend frontend | Out-Null
    throw
}
