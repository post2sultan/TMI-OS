




param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\P1-05"
$Patch = Join-Path $Release "patch"
$BackupRoot = Join-Path $Release "backups"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Backup = Join-Path $BackupRoot $Timestamp
$LatestBackupFile = Join-Path $Release ".latest-backup.txt"
$ComposeFile = Join-Path $Root "docker\compose.yml"
$BaseUrl = "http://127.0.0.1:8000"

$Targets = @(
    "backend\app\main.py",
    "backend\app\services\analysis\review_service.py",
    "backend\app\services\campaign_lifecycle.py",
    "backend\alembic\versions\f2c5d7e9a1b3_add_campaign_status_lifecycle.py",
    "backend\tests\test_campaign_lifecycle.py",
    "docs\BACKLOG.md"
)

function Wait-Endpoint {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [int]$Attempts = 40
    )

    for ($Attempt = 1; $Attempt -le $Attempts; $Attempt++) {
        try {
            return Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 5
        }
        catch {
            if ($Attempt -eq $Attempts) {
                throw "Endpoint did not become available: $Url"
            }
            Start-Sleep -Seconds 2
        }
    }
}

function Restore-Backup {
    if (-not (Test-Path $Backup)) {
        return
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
    }
}

try {
    if (-not (Test-Path $ComposeFile)) {
        throw "Compose file not found: $ComposeFile"
    }

    New-Item -ItemType Directory -Force -Path $Backup | Out-Null

    foreach ($RelativePath in $Targets) {
        $SourcePath = Join-Path $Patch $RelativePath
        $TargetPath = Join-Path $Root $RelativePath
        $BackupPath = Join-Path $Backup $RelativePath

        if (-not (Test-Path $SourcePath)) {
            throw "Patch file missing: $SourcePath"
        }

        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $BackupPath) | Out-Null

        if (Test-Path $TargetPath) {
            Copy-Item -Force $TargetPath $BackupPath
        }
        else {
            New-Item -ItemType File -Force -Path "$BackupPath.__missing__" | Out-Null
        }
    }

    Set-Content -Path $LatestBackupFile -Value $Backup -Encoding UTF8

    foreach ($RelativePath in $Targets) {
        $SourcePath = Join-Path $Patch $RelativePath
        $TargetPath = Join-Path $Root $RelativePath
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $TargetPath) | Out-Null
        Copy-Item -Force $SourcePath $TargetPath
    }

    docker compose -f $ComposeFile exec -T backend python -B -c "import ast,pathlib; files=['/app/app/main.py','/app/app/services/analysis/review_service.py','/app/app/services/campaign_lifecycle.py','/app/alembic/versions/f2c5d7e9a1b3_add_campaign_status_lifecycle.py','/app/tests/test_campaign_lifecycle.py']; [ast.parse(pathlib.Path(f).read_text(encoding='utf-8-sig'), filename=f) for f in files]; print('SYNTAX_OK')"
    if ($LASTEXITCODE -ne 0) {
        throw "Python syntax validation failed."
    }

    docker compose -f $ComposeFile exec -T backend alembic upgrade head
    if ($LASTEXITCODE -ne 0) {
        throw "Campaign-lifecycle migration failed."
    }

    docker compose -f $ComposeFile restart backend
    if ($LASTEXITCODE -ne 0) {
        throw "Backend restart failed."
    }

    Wait-Endpoint -Url "$BaseUrl/health" | Out-Null
    Wait-Endpoint -Url "$BaseUrl/ready" | Out-Null

    docker compose -f $ComposeFile exec -T backend python -B -m unittest discover -s /app/tests -p "test_*.py" -v
    if ($LASTEXITCODE -ne 0) {
        throw "P1-05 test suite failed."
    }

    Write-Host ""
    Write-Host "P1-05 installation PASSED."
    Write-Host "Backup: $Backup"
}
catch {
    Write-Host ""
    Write-Host "P1-05 installation FAILED. Rolling back..." -ForegroundColor Red
    try {
        docker compose -f $ComposeFile exec -T backend alembic downgrade e1b4c6d8f0a2 | Out-Null
    }
    catch {
    }

    Restore-Backup

    try {
        docker compose -f $ComposeFile restart backend | Out-Null
    }
    catch {
    }

    throw
}
