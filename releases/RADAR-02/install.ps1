param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\RADAR-02"
$Backup = Join-Path $Release "backups\$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$LatestBackupFile = Join-Path $Release ".latest-backup.txt"
$ComposeFile = Join-Path $Root "docker\compose.yml"
$Targets = @(
    "backend/app/services/discovery/manager.py",
    "backend/tests/test_discovery_google_news_links.py"
)

function Restore-Backup {
    foreach ($RelativePath in $Targets) {
        $Target = Join-Path $Root $RelativePath
        $Stored = Join-Path $Backup $RelativePath
        if (Test-Path $Stored) {
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Target) | Out-Null
            Copy-Item -Force $Stored $Target
        }
        elseif (Test-Path "$Stored.__missing__") {
            Remove-Item -Force -ErrorAction SilentlyContinue $Target
        }
    }
}

try {
    foreach ($RelativePath in $Targets) {
        $Stored = Join-Path $Backup $RelativePath
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Stored) | Out-Null
        $Tracked = git -C $Root ls-files --cached -- $RelativePath
        if (($Tracked | Out-String).Trim()) {
            $Committed = git -C $Root show "HEAD:$RelativePath"
            if ($LASTEXITCODE -ne 0) {
                throw "Could not read committed backup source: $RelativePath"
            }
            Set-Content -LiteralPath $Stored -Value $Committed -Encoding utf8
        }
        else {
            New-Item -ItemType File -Force -Path "$Stored.__missing__" | Out-Null
        }
    }
    Set-Content -LiteralPath $LatestBackupFile -Value $Backup -Encoding utf8

    docker compose -f $ComposeFile restart backend
    if ($LASTEXITCODE -ne 0) {
        throw "Backend restart failed."
    }

    & (Join-Path $Release "validate.ps1") -Root $Root

    Write-Host ""
    Write-Host "RADAR-02 installation PASSED."
    Write-Host "Backup: $Backup"
}
catch {
    Write-Host ""
    Write-Host "RADAR-02 installation FAILED. Rolling back..." -ForegroundColor Red
    Restore-Backup
    try {
        docker compose -f $ComposeFile restart backend | Out-Null
    }
    catch {
    }
    throw
}
