param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\P1-06"
$Patch = Join-Path $Release "patch"
$BackupRoot = Join-Path $Release "backups"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Backup = Join-Path $BackupRoot $Timestamp
$LatestBackupFile = Join-Path $Release ".latest-backup.txt"
$ComposeFile = Join-Path $Root "docker\compose.yml"
$BaseUrl = "http://127.0.0.1:8000"
$Targets = @(
    "backend\app\routers\reviews.py",
    "backend\app\schemas\review.py",
    "backend\app\services\analysis\review_service.py",
    "backend\app\services\campaign_lifecycle.py",
    "backend\tests\test_campaign_review_api.py",
    "docs\BACKLOG.md"
)

function Wait-Endpoint {
    param([Parameter(Mandatory = $true)][string]$Url)
    for ($Attempt = 1; $Attempt -le 40; $Attempt++) {
        try { return Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 5 }
        catch {
            if ($Attempt -eq 40) { throw "Endpoint did not become available: $Url" }
            Start-Sleep -Seconds 2
        }
    }
}

function Restore-Backup {
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
    }
}

try {
    if (-not (Test-Path $ComposeFile)) { throw "Compose file not found: $ComposeFile" }
    New-Item -ItemType Directory -Force -Path $Backup | Out-Null

    foreach ($RelativePath in $Targets) {
        $SourcePath = Join-Path $Patch $RelativePath
        $TargetPath = Join-Path $Root $RelativePath
        $BackupPath = Join-Path $Backup $RelativePath
        if (-not (Test-Path $SourcePath)) { throw "Patch file missing: $SourcePath" }
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

    docker compose -f $ComposeFile exec -T backend python -B -c "import ast,pathlib; files=['/app/app/routers/reviews.py','/app/app/schemas/review.py','/app/app/services/analysis/review_service.py','/app/app/services/campaign_lifecycle.py','/app/tests/test_campaign_review_api.py']; [ast.parse(pathlib.Path(f).read_text(encoding='utf-8-sig'), filename=f) for f in files]; print('SYNTAX_OK')"
    if ($LASTEXITCODE -ne 0) { throw "Python syntax validation failed." }

    docker compose -f $ComposeFile restart backend
    if ($LASTEXITCODE -ne 0) { throw "Backend restart failed." }
    Wait-Endpoint -Url "$BaseUrl/health" | Out-Null
    Wait-Endpoint -Url "$BaseUrl/ready" | Out-Null

    docker compose -f $ComposeFile exec -T backend python -B -m unittest discover -s /app/tests -p "test_*.py" -q
    if ($LASTEXITCODE -ne 0) { throw "P1-06 test suite failed." }

    Write-Host ""
    Write-Host "P1-06 installation PASSED."
    Write-Host "Backup: $Backup"
}
catch {
    Write-Host ""
    Write-Host "P1-06 installation FAILED. Rolling back..." -ForegroundColor Red
    Restore-Backup
    try { docker compose -f $ComposeFile restart backend | Out-Null } catch {}
    throw
}
