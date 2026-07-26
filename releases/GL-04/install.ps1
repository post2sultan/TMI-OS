param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\GL-04"
$Patch = Join-Path $Release "patch"
$Backup = Join-Path (Join-Path $Release "backups") (Get-Date -Format "yyyyMMdd-HHmmss")
$LatestBackupFile = Join-Path $Release ".latest-backup.txt"
$DataTestRoot = Join-Path $Root ".gl04-validation"
$Targets = @(
    "docker\production.env.example",
    "docs\DATA_RECOVERY.md",
    "docs\GO_LIVE.md",
    "scripts\backup-data.ps1",
    "scripts\validate-data-restore.ps1"
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
    New-Item -ItemType Directory -Force $Backup | Out-Null
    foreach ($RelativePath in $Targets) {
        $Source = Join-Path $Patch $RelativePath
        $Destination = Join-Path $Root $RelativePath
        $Saved = Join-Path $Backup $RelativePath
        if (-not (Test-Path $Source)) { throw "Patch file missing: $Source" }
        New-Item -ItemType Directory -Force (Split-Path -Parent $Saved) | Out-Null
        if (Test-Path $Destination) { Copy-Item -Force $Destination $Saved }
        else { New-Item -ItemType File -Force "$Saved.__missing__" | Out-Null }
    }
    Set-Content $LatestBackupFile $Backup -Encoding UTF8
    foreach ($RelativePath in $Targets) {
        $Source = Join-Path $Patch $RelativePath
        $Destination = Join-Path $Root $RelativePath
        New-Item -ItemType Directory -Force (Split-Path -Parent $Destination) | Out-Null
        Copy-Item -Force $Source $Destination
    }

    [void][scriptblock]::Create((Get-Content (Join-Path $Root "scripts\backup-data.ps1") -Raw))
    [void][scriptblock]::Create((Get-Content (Join-Path $Root "scripts\validate-data-restore.ps1") -Raw))
    & (Join-Path $Root "scripts\backup-data.ps1") -Root $Root -OutputRoot $DataTestRoot
    $LatestDataBackup = Get-ChildItem $DataTestRoot -Directory |
        Where-Object Name -match '^\d{8}T\d{6}Z$' |
        Sort-Object Name -Descending | Select-Object -First 1
    if (-not $LatestDataBackup) { throw "GL-04 data backup was not created." }
    & (Join-Path $Root "scripts\validate-data-restore.ps1") `
        -BackupPath $LatestDataBackup.FullName
    Write-Host "GL-04 installation PASSED."
    Write-Host "Source backup: $Backup"
}
catch {
    Write-Host "GL-04 installation FAILED. Rolling back..." -ForegroundColor Red
    Restore-SourceBackup
    throw
}
