$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ReleaseRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = "O:\TMI-OS"
$ComposeFile = Join-Path $ProjectRoot "docker\compose.yml"
$PatchRoot = Join-Path $ReleaseRoot "patch"
$BackupRoot = Join-Path $ReleaseRoot ("backups\" + (Get-Date -Format "yyyyMMdd-HHmmss"))

$Files = @(
    "backend\app\main.py",
    "backend\app\repositories\discovery_run_repository.py"
)

function Restore-Backup {
    param([string]$BackupPath)

    Write-Host "Restoring backup..." -ForegroundColor Yellow

    foreach ($relativePath in $Files) {
        $destination = Join-Path $ProjectRoot $relativePath
        $backupFile = Join-Path $BackupPath $relativePath
        $marker = "$backupFile.__NEW_FILE__"

        if (Test-Path $backupFile) {
            New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
            Copy-Item $backupFile $destination -Force
        }
        elseif (Test-Path $marker) {
            Remove-Item $destination -Force -ErrorAction SilentlyContinue
        }
    }

    docker compose -f $ComposeFile restart backend | Out-Host
}

function Wait-ForEndpoint {
    param(
        [string]$Uri,
        [int]$Attempts = 30,
        [int]$DelaySeconds = 2
    )

    for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
        try {
            $response = Invoke-RestMethod -Uri $Uri -Method Get -TimeoutSec 10
            return $response
        }
        catch {
            if ($attempt -eq $Attempts) {
                throw "Endpoint did not become ready: $Uri"
            }

            Start-Sleep -Seconds $DelaySeconds
        }
    }
}

Write-Host "M3.1a - Installing DiscoveryRun persistence..." -ForegroundColor Cyan

if (-not (Test-Path $ComposeFile)) {
    throw "Compose file not found: $ComposeFile"
}

foreach ($relativePath in $Files) {
    $source = Join-Path $PatchRoot $relativePath
    if (-not (Test-Path $source)) {
        throw "Patch file missing: $source"
    }
}

New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null

try {
    foreach ($relativePath in $Files) {
        $source = Join-Path $PatchRoot $relativePath
        $destination = Join-Path $ProjectRoot $relativePath
        $backupFile = Join-Path $BackupRoot $relativePath

        New-Item -ItemType Directory -Path (Split-Path -Parent $backupFile) -Force | Out-Null
        New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null

        if (Test-Path $destination) {
            Copy-Item $destination $backupFile -Force
        }
        else {
            New-Item -ItemType File -Path "$backupFile.__NEW_FILE__" -Force | Out-Null
        }

        Copy-Item $source $destination -Force
        Write-Host "Installed: $relativePath" -ForegroundColor Green
    }

    Write-Host "Checking Python syntax without writing bytecode..." -ForegroundColor Yellow
    docker exec -e PYTHONDONTWRITEBYTECODE=1 tmi-backend python -B -c "import ast, pathlib; files=['/app/app/main.py','/app/app/repositories/discovery_run_repository.py']; [ast.parse(pathlib.Path(f).read_text(encoding='utf-8'), filename=f) for f in files]; print('SYNTAX_OK')" | Out-Host

    if ($LASTEXITCODE -ne 0) {
        throw "Python syntax validation failed."
    }

    Write-Host "Restarting backend..." -ForegroundColor Yellow
    docker compose -f $ComposeFile restart backend | Out-Host

    Write-Host "Waiting for backend health..." -ForegroundColor Yellow
    $health = Wait-ForEndpoint -Uri "http://localhost:8000/health"
    $ready = Wait-ForEndpoint -Uri "http://localhost:8000/ready"

    Write-Host "Checking application import..." -ForegroundColor Yellow
    docker exec -e PYTHONDONTWRITEBYTECODE=1 tmi-backend python -B -c "from app.main import app; from app.repositories.discovery_run_repository import discovery_run_repository; print(app.title); print(type(discovery_run_repository).__name__)" | Out-Host

    if ($LASTEXITCODE -ne 0) {
        throw "Backend import validation failed."
    }

    $latestBackupFile = Join-Path $ReleaseRoot ".latest-backup.txt"
    Set-Content -Path $latestBackupFile -Value $BackupRoot -Encoding UTF8

    Write-Host ""
    Write-Host "M3.1a installation completed successfully." -ForegroundColor Green
    Write-Host "Next command:" -ForegroundColor Cyan
    Write-Host "powershell -ExecutionPolicy Bypass -File `"$ReleaseRoot\validate.ps1`"" -ForegroundColor White
}
catch {
    Write-Host "Installation failed: $($_.Exception.Message)" -ForegroundColor Red
    Restore-Backup -BackupPath $BackupRoot
    throw
}
