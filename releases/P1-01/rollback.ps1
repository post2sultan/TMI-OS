
param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\P1-01"
$LatestBackupFile = Join-Path $Release ".latest-backup.txt"
$ComposeFile = Join-Path $Root "docker\compose.yml"
$BaseUrl = "http://127.0.0.1:8000"

$Targets = @(
    "backend\app\models\campaign_document.py",
    "backend\app\models\__init__.py",
    "backend\app\repositories\campaign_document_repository.py",
    "backend\alembic\env.py",
    "backend\alembic\versions\b8e1f2a3c4d5_add_campaign_source_documents.py",
    "backend\tests\test_campaign_document_repository.py",
    "docs\BACKLOG.md"
)

if (-not (Test-Path $LatestBackupFile)) {
    throw "No P1-01 backup reference exists."
}

$Backup = (Get-Content $LatestBackupFile -Raw).Trim()
if (-not $Backup -or -not (Test-Path $Backup)) {
    throw "P1-01 backup folder not found: $Backup"
}

docker compose -f $ComposeFile exec -T backend alembic downgrade 9c7b2d4e6f80
if ($LASTEXITCODE -ne 0) {
    throw "Campaign-document migration rollback failed."
}

foreach ($RelativePath in $Targets) {
    $BackupPath = Join-Path $Backup $RelativePath
    $TargetPath = Join-Path $Root $RelativePath
    $MissingMarker = "$BackupPath.__missing__"

    if (Test-Path $BackupPath) {
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $TargetPath) | Out-Null
        Copy-Item -Force $BackupPath $TargetPath
    }
    elseif (Test-Path $MissingMarker) {
        Remove-Item -Force -ErrorAction SilentlyContinue $TargetPath
    }
    else {
        throw "Backup entry missing for: $RelativePath"
    }
}

docker compose -f $ComposeFile restart backend
if ($LASTEXITCODE -ne 0) {
    throw "Backend restart failed after rollback."
}

for ($Attempt = 1; $Attempt -le 40; $Attempt++) {
    try {
        $Health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get -TimeoutSec 5
        if ($Health.status -eq "healthy") {
            Write-Host "P1-01 rollback PASSED."
            Write-Host "Restored backup: $Backup"
            exit 0
        }
    }
    catch {
    }
    Start-Sleep -Seconds 2
}

throw "Backend did not become healthy after rollback."
