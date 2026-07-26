param(
    [string]$ProjectRoot = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ReleaseRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackupRoot = Join-Path $ReleaseRoot "backups"
$ComposeFile = Join-Path $ProjectRoot "docker\compose.yml"

if (-not (Test-Path $BackupRoot)) {
    throw "No M3.1a backups found."
}

$BackupFolder = Get-ChildItem -Path $BackupRoot -Directory |
    Sort-Object Name -Descending |
    Select-Object -First 1

if ($null -eq $BackupFolder) {
    throw "No M3.1a backup folder found."
}

$ManifestPath = Join-Path $BackupFolder.FullName "manifest.json"
if (-not (Test-Path $ManifestPath)) {
    throw "Backup manifest not found: $ManifestPath"
}

$Manifest = Get-Content -Path $ManifestPath -Raw | ConvertFrom-Json

Write-Host "Rolling back M3.1a using: $($BackupFolder.FullName)"

foreach ($Item in $Manifest) {
    $TargetFile = Join-Path $ProjectRoot $Item.RelativePath
    $BackupFile = Join-Path $BackupFolder.FullName $Item.RelativePath

    if ($Item.Existed) {
        $TargetParent = Split-Path -Parent $TargetFile
        New-Item -ItemType Directory -Force -Path $TargetParent | Out-Null
        Copy-Item -Path $BackupFile -Destination $TargetFile -Force
        Write-Host "Restored: $($Item.RelativePath)"
    }
    elseif (Test-Path $TargetFile) {
        Remove-Item -Path $TargetFile -Force
        Write-Host "Removed: $($Item.RelativePath)"
    }
}

& docker compose -f $ComposeFile restart backend
if ($LASTEXITCODE -ne 0) {
    throw "Backend restart failed after rollback."
}

Write-Host ""
Write-Host "M3.1a rollback completed."
