param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\M3.1b"
$Patch = Join-Path $Release "patch"
$BackupRoot = Join-Path $Release "backups"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Backup = Join-Path $BackupRoot $Timestamp
$LatestBackupFile = Join-Path $Release ".latest-backup.txt"
$ComposeFile = Join-Path $Root "docker\compose.yml"
$BaseUrl = "http://127.0.0.1:8000"

$Targets = @(
    "backend\app\main.py",
    "backend\app\repositories\discovery_run_repository.py",
    "backend\app\routers\discovery_history.py",
    "backend\app\schemas\discovery_history.py"
)

function Wait-Endpoint {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [int]$Attempts = 40,
        [int]$DelaySeconds = 2
    )

    for ($Attempt = 1; $Attempt -le $Attempts; $Attempt++) {
        try {
            $Response = Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 5
            return $Response
        }
        catch {
            if ($Attempt -eq $Attempts) {
                throw "Endpoint did not become available: $Url"
            }

            Start-Sleep -Seconds $DelaySeconds
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

    $PythonFiles = $Targets | Where-Object { $_.EndsWith(".py") }

    foreach ($RelativePath in $PythonFiles) {
        $ContainerPath = "/app/" + ($RelativePath -replace "^backend\\", "" -replace "\\", "/")
        docker compose -f $ComposeFile exec -T backend python -B -c "import ast, pathlib; ast.parse(pathlib.Path('$ContainerPath').read_text(encoding='utf-8')); print('SYNTAX_OK: $ContainerPath')"

        if ($LASTEXITCODE -ne 0) {
            throw "Python syntax validation failed: $RelativePath"
        }
    }

    docker compose -f $ComposeFile restart backend

    if ($LASTEXITCODE -ne 0) {
        throw "Backend restart failed."
    }

    Wait-Endpoint -Url "$BaseUrl/health" | Out-Null
    Wait-Endpoint -Url "$BaseUrl/ready" | Out-Null

    docker compose -f $ComposeFile exec -T backend python -B -c "from app.main import app; assert any(route.path == '/discovery/history' for route in app.routes); print('ROUTE_OK: /discovery/history')"

    if ($LASTEXITCODE -ne 0) {
        throw "Runtime route validation failed."
    }

    Write-Host ""
    Write-Host "M3.1b installation PASSED."
    Write-Host "Backup: $Backup"
}
catch {
    Write-Host ""
    Write-Host "M3.1b installation FAILED. Rolling back..." -ForegroundColor Red

    Restore-Backup

    try {
        docker compose -f $ComposeFile restart backend | Out-Null
    }
    catch {
    }

    throw
}