

param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\P1-02"
$LatestBackupFile = Join-Path $Release ".latest-backup.txt"
$ComposeFile = Join-Path $Root "docker\compose.yml"
$BaseUrl = "http://127.0.0.1:8000"

$Targets = @(
    "backend\app\api\extraction.py",
    "backend\app\models\campaign_document.py",
    "backend\app\repositories\campaign_document_repository.py",
    "backend\alembic\versions\c9f2a4b6d8e0_add_structured_evidence_extraction.py",
    "backend\tests\test_campaign_document_repository.py",
    "backend\tests\test_campaign_evidence_extraction.py",
    "docs\BACKLOG.md"
)

if (-not (Test-Path $LatestBackupFile)) {
    throw "No P1-02 backup reference exists."
}

$Backup = (Get-Content $LatestBackupFile -Raw).Trim()
if (-not $Backup -or -not (Test-Path $Backup)) {
    throw "P1-02 backup folder not found: $Backup"
}

docker compose -f $ComposeFile exec -T backend alembic downgrade b8e1f2a3c4d5
if ($LASTEXITCODE -ne 0) {
    throw "Evidence-extraction migration rollback failed."
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
            Write-Host "P1-02 rollback PASSED."
            Write-Host "Restored backup: $Backup"
            exit 0
        }
    }
    catch {
    }
    Start-Sleep -Seconds 2
}

throw "Backend did not become healthy after rollback."
