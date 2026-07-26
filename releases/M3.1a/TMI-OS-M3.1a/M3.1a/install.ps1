param(
    [string]$ProjectRoot = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ReleaseRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PatchRoot = Join-Path $ReleaseRoot "patch"
$ComposeFile = Join-Path $ProjectRoot "docker\compose.yml"
$BackupRoot = Join-Path $ReleaseRoot "backups"
$BackupFolder = Join-Path $BackupRoot (Get-Date -Format "yyyyMMdd-HHmmss")

$Files = @(
    "backend\app\main.py",
    "backend\app\repositories\discovery_run_repository.py"
)

Write-Host "M3.1a - Installing DiscoveryRun persistence..."

if (-not (Test-Path $ProjectRoot)) {
    throw "Project root not found: $ProjectRoot"
}

if (-not (Test-Path $ComposeFile)) {
    throw "Docker Compose file not found: $ComposeFile"
}

foreach ($RelativePath in $Files) {
    $PatchFile = Join-Path $PatchRoot $RelativePath
    if (-not (Test-Path $PatchFile)) {
        throw "Release patch file missing: $PatchFile"
    }
}

New-Item -ItemType Directory -Force -Path $BackupFolder | Out-Null
$Manifest = @()

foreach ($RelativePath in $Files) {
    $TargetFile = Join-Path $ProjectRoot $RelativePath
    $BackupFile = Join-Path $BackupFolder $RelativePath
    $Existed = Test-Path $TargetFile

    $Manifest += [pscustomobject]@{
        RelativePath = $RelativePath
        Existed = $Existed
    }

    if ($Existed) {
        $BackupParent = Split-Path -Parent $BackupFile
        New-Item -ItemType Directory -Force -Path $BackupParent | Out-Null
        Copy-Item -Path $TargetFile -Destination $BackupFile -Force
    }
}

$Manifest | ConvertTo-Json | Set-Content -Path (Join-Path $BackupFolder "manifest.json") -Encoding UTF8

try {
    foreach ($RelativePath in $Files) {
        $PatchFile = Join-Path $PatchRoot $RelativePath
        $TargetFile = Join-Path $ProjectRoot $RelativePath
        $TargetParent = Split-Path -Parent $TargetFile

        New-Item -ItemType Directory -Force -Path $TargetParent | Out-Null
        Copy-Item -Path $PatchFile -Destination $TargetFile -Force
        Write-Host "Installed: $RelativePath"
    }

    & docker compose -f $ComposeFile config --quiet
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose validation failed."
    }

    & docker compose -f $ComposeFile exec -T backend python -m compileall -q /app/app
    if ($LASTEXITCODE -ne 0) {
        throw "Backend Python compilation failed."
    }

    & docker compose -f $ComposeFile restart backend
    if ($LASTEXITCODE -ne 0) {
        throw "Backend restart failed."
    }

    Write-Host ""
    Write-Host "M3.1a installed successfully."
    Write-Host "Backup: $BackupFolder"
    Write-Host "Next: run .\validate.ps1"
}
catch {
    Write-Host "Installation failed. Restoring backup..." -ForegroundColor Red

    foreach ($Item in $Manifest) {
        $TargetFile = Join-Path $ProjectRoot $Item.RelativePath
        $BackupFile = Join-Path $BackupFolder $Item.RelativePath

        if ($Item.Existed) {
            Copy-Item -Path $BackupFile -Destination $TargetFile -Force
        }
        elseif (Test-Path $TargetFile) {
            Remove-Item -Path $TargetFile -Force
        }
    }

    & docker compose -f $ComposeFile restart backend | Out-Null
    throw
}
