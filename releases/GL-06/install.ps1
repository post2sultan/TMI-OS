param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\GL-06"
$Payload = Join-Path $Release "payload"
$Backup = Join-Path (Join-Path $Release "backups") (Get-Date -Format "yyyyMMdd-HHmmss")
$Reference = Join-Path $Release ".latest-backup.txt"
$Targets = @(
    "backend\app\core\settings.py",
    "backend\app\main.py",
    "backend\app\observability.py",
    "backend\app\security.py",
    "backend\tests\test_observability.py",
    "docker\compose.production.yml",
    "docker\production.env.example",
    "docs\GO_LIVE.md",
    "docs\OBSERVABILITY.md",
    "monitoring\alerts.yml",
    "monitoring\blackbox.yml",
    "monitoring\prometheus.yml",
    "scripts\validate-observability.ps1"
)

function Restore-SourceBackup {
    foreach ($RelativePath in $Targets) {
        $Saved = Join-Path $Backup $RelativePath
        $Destination = Join-Path $Root $RelativePath
        if (Test-Path $Saved) {
            New-Item -ItemType Directory -Force (Split-Path -Parent $Destination) | Out-Null
            Copy-Item -Force $Saved $Destination
        }
        elseif (Test-Path "$Saved.__missing__") {
            Remove-Item -Force -ErrorAction SilentlyContinue $Destination
        }
    }
}

try {
    if (-not (Test-Path $Payload)) {
        New-Item -ItemType Directory -Force $Payload | Out-Null
        foreach ($RelativePath in $Targets) {
            $Source = Join-Path $Root $RelativePath
            $Destination = Join-Path $Payload $RelativePath
            if (-not (Test-Path $Source)) { throw "Release source missing: $Source" }
            New-Item -ItemType Directory -Force (Split-Path -Parent $Destination) | Out-Null
            Copy-Item -Force $Source $Destination
        }
    }

    New-Item -ItemType Directory -Force $Backup | Out-Null
    foreach ($RelativePath in $Targets) {
        $Destination = Join-Path $Root $RelativePath
        $Saved = Join-Path $Backup $RelativePath
        New-Item -ItemType Directory -Force (Split-Path -Parent $Saved) | Out-Null
        $GitPath = $RelativePath.Replace("\", "/")
        $Tracked = git -C $Root ls-tree --name-only HEAD -- $GitPath
        if (($Tracked | Out-String).Trim()) {
            $Baseline = git -C $Root show "HEAD:$GitPath"
            [System.IO.File]::WriteAllLines($Saved, $Baseline)
        }
        else {
            New-Item -ItemType File -Force "$Saved.__missing__" | Out-Null
        }
    }
    Set-Content $Reference $Backup -Encoding UTF8

    foreach ($RelativePath in $Targets) {
        $Source = Join-Path $Payload $RelativePath
        $Destination = Join-Path $Root $RelativePath
        New-Item -ItemType Directory -Force (Split-Path -Parent $Destination) | Out-Null
        Copy-Item -Force $Source $Destination
    }

    docker compose -f (Join-Path $Root "docker\compose.yml") restart backend
    if ($LASTEXITCODE -ne 0) { throw "Backend restart failed." }
    & (Join-Path $Root "releases\GL-06\validate.ps1") -Root $Root
    Write-Host "GL-06 installation PASSED."
    Write-Host "Backup: $Backup"
}
catch {
    Write-Host "GL-06 installation FAILED. Rolling back..." -ForegroundColor Red
    Restore-SourceBackup
    docker compose -f (Join-Path $Root "docker\compose.yml") restart backend
    throw
}
