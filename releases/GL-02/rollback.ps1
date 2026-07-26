param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\GL-02"
$LatestBackupFile = Join-Path $Release ".latest-backup.txt"
$ComposeFile = Join-Path $Root "docker\compose.yml"
$BaseUrl = "http://127.0.0.1:8000"
$Targets = @(
    "backend\.env.example",
    "backend\Dockerfile",
    "backend\.dockerignore",
    "backend\app\core\settings.py",
    "backend\app\services\vector\qdrant_service.py",
    "backend\app\services\prompt_service.py",
    "backend\tests\test_production_configuration.py",
    "backend\tests\test_prompt_packaging.py",
    "docker\production.env.example",
    "docker\compose.production.yml",
    "scripts\validate-production-container.ps1",
    "docs\GO_LIVE.md"
)

if (-not (Test-Path $LatestBackupFile)) {
    throw "No GL-02 backup reference exists."
}
$Backup = (Get-Content $LatestBackupFile -Raw).Trim()
if (-not $Backup -or -not (Test-Path $Backup)) {
    throw "GL-02 backup folder not found: $Backup"
}

foreach ($RelativePath in $Targets) {
    $BackupPath = Join-Path $Backup $RelativePath
    $TargetPath = Join-Path $Root $RelativePath
    if (Test-Path $BackupPath) {
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $TargetPath) | Out-Null
        Copy-Item -Force $BackupPath $TargetPath
    }
    elseif (Test-Path "$BackupPath.__missing__") {
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
            Write-Host "GL-02 rollback PASSED."
            Write-Host "Restored backup: $Backup"
            exit 0
        }
    }
    catch {
    }
    Start-Sleep -Seconds 2
}

throw "Backend did not become healthy after rollback."
