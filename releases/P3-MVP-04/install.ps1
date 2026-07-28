param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
$Release = Join-Path $Root "releases\P3-MVP-04"
$EnvFile = Join-Path $Root "docker\.env.production.local"
$ComposeFile = Join-Path $Root "docker\compose.production.yml"
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$CleanRoot = Join-Path $Root "tmp\p3-mvp-04-$Stamp"
$BackupDir = Join-Path $Release "backups\$Stamp"
$Archive = Join-Path $CleanRoot "source.zip"
$TagLine = Get-Content $EnvFile | Where-Object { $_ -match "^TMI_RELEASE_TAG=" } | Select-Object -First 1
$Tag = ($TagLine -split "=",2)[1].Trim()
$Backend = "tmi-os-backend:$Tag"; $Frontend = "tmi-os-frontend:$Tag"
$BackendBackup = "tmi-os-backend:pre-p3-mvp-04-$Stamp"
$FrontendBackup = "tmi-os-frontend:pre-p3-mvp-04-$Stamp"
New-Item -ItemType Directory -Force -Path $CleanRoot,$BackupDir | Out-Null
git -C $Root archive --format=zip "--output=$Archive" HEAD backend frontend
Expand-Archive $Archive $CleanRoot
docker image tag $Backend $BackendBackup; docker image tag $Frontend $FrontendBackup
Set-Content (Join-Path $Release ".production-backend-image.txt") $BackendBackup
Set-Content (Join-Path $Release ".production-frontend-image.txt") $FrontendBackup
$DbBackup = "p3-mvp-04-$Stamp.sql"
docker exec tmi-production-postgres-1 sh -c "pg_dump -U `"`$POSTGRES_USER`" `"`$POSTGRES_DB`" > /tmp/$DbBackup"
docker cp "tmi-production-postgres-1:/tmp/$DbBackup" (Join-Path $BackupDir $DbBackup)
try {
    docker build -t $Backend (Join-Path $CleanRoot "backend")
    if ($LASTEXITCODE -ne 0) { throw "Backend build failed." }
    docker build -t $Frontend (Join-Path $CleanRoot "frontend")
    if ($LASTEXITCODE -ne 0) { throw "Frontend build failed." }
    docker compose --env-file $EnvFile --project-name tmi-production -f $ComposeFile up -d --no-deps --wait backend frontend
    if ($LASTEXITCODE -ne 0) { throw "Deployment failed." }
    & (Join-Path $Release "validate.ps1") -Root $Root
} catch {
    docker image tag $BackendBackup $Backend | Out-Null
    docker image tag $FrontendBackup $Frontend | Out-Null
    docker compose --env-file $EnvFile --project-name tmi-production -f $ComposeFile up -d --no-deps --wait backend frontend | Out-Null
    throw
}
Write-Host "P3-MVP-04 installation PASSED."
