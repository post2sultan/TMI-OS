param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$Release = Join-Path $Root "releases\P1-06"
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

if (-not (Test-Path $LatestBackupFile)) { throw "No P1-06 backup reference exists." }
$Backup = (Get-Content $LatestBackupFile -Raw).Trim()
if (-not $Backup -or -not (Test-Path $Backup)) { throw "P1-06 backup folder not found: $Backup" }

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
if ($LASTEXITCODE -ne 0) { throw "Backend restart failed after rollback." }

for ($Attempt = 1; $Attempt -le 40; $Attempt++) {
    try {
        $Health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get -TimeoutSec 5
        if ($Health.status -eq "healthy") {
            Write-Host "P1-06 rollback PASSED."
            Write-Host "Restored backup: $Backup"
            exit 0
        }
    }
    catch {}
    Start-Sleep -Seconds 2
}

throw "Backend did not become healthy after rollback."
