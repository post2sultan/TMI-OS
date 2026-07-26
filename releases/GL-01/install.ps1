




param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\GL-01"
$Patch = Join-Path $Release "patch"
$BackupRoot = Join-Path $Release "backups"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Backup = Join-Path $BackupRoot $Timestamp
$LatestBackupFile = Join-Path $Release ".latest-backup.txt"
$ComposeFile = Join-Path $Root "docker\compose.yml"
$BaseUrl = "http://127.0.0.1:8000"

$Targets = @(
    "backend\.env.example",
    "backend\app\core\settings.py",
    "backend\app\main.py",
    "backend\app\security.py",
    "backend\app\models\__init__.py",
    "backend\app\models\audit_event.py",
    "backend\alembic\env.py",
    "backend\alembic\versions\c5f8a1d3e6b9_add_security_audit_events.py",
    "backend\tests\test_security.py",
    "backend\tests\test_analysis_quality_validator.py",
    "frontend\.env.example",
    "frontend\src\lib\api.ts",
    "docs\GO_LIVE.md"
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

    docker compose -f $ComposeFile exec -T backend python -B -c "import ast,pathlib; files=['/app/app/core/settings.py','/app/app/main.py','/app/app/security.py','/app/app/models/__init__.py','/app/app/models/audit_event.py','/app/alembic/env.py','/app/alembic/versions/c5f8a1d3e6b9_add_security_audit_events.py','/app/tests/test_security.py','/app/tests/test_analysis_quality_validator.py']; [ast.parse(pathlib.Path(f).read_text(encoding='utf-8-sig'), filename=f) for f in files]; print('SYNTAX_OK')"
    if ($LASTEXITCODE -ne 0) {
        throw "Python syntax validation failed."
    }

    docker compose -f $ComposeFile exec -T backend alembic upgrade head
    if ($LASTEXITCODE -ne 0) {
        throw "Security audit migration failed."
    }

    docker compose -f $ComposeFile restart backend
    if ($LASTEXITCODE -ne 0) {
        throw "Backend restart failed."
    }

    Wait-Endpoint -Url "$BaseUrl/health" | Out-Null
    Wait-Endpoint -Url "$BaseUrl/ready" | Out-Null

    docker compose -f $ComposeFile exec -T backend python -B -m unittest discover -s /app/tests -p "test_*.py" -v
    if ($LASTEXITCODE -ne 0) {
        throw "GL-01 test suite failed."
    }

    Push-Location (Join-Path $Root "frontend")
    try {
        npm.cmd run build
        if ($LASTEXITCODE -ne 0) { throw "Frontend build failed." }
        npm.cmd run lint
        if ($LASTEXITCODE -ne 0) { throw "Frontend lint failed." }
    }
    finally {
        Pop-Location
    }

    Write-Host ""
    Write-Host "GL-01 installation PASSED."
    Write-Host "Backup: $Backup"
}
catch {
    Write-Host ""
    Write-Host "GL-01 installation FAILED. Rolling back..." -ForegroundColor Red
    try {
        docker compose -f $ComposeFile exec -T backend alembic downgrade a3d6f8b0c2e4 | Out-Null
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
