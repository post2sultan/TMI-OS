param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\GL-04"
$Reference = Join-Path $Release ".latest-backup.txt"
$Targets = @(
    "docker\production.env.example",
    "docs\DATA_RECOVERY.md",
    "docs\GO_LIVE.md",
    "scripts\backup-data.ps1",
    "scripts\validate-data-restore.ps1"
)
if (-not (Test-Path $Reference)) { throw "No GL-04 source backup reference exists." }
$Backup = (Get-Content $Reference -Raw).Trim()
if (-not (Test-Path $Backup)) { throw "GL-04 source backup not found: $Backup" }

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
    else { throw "Backup entry missing for: $RelativePath" }
}

$Health = Invoke-RestMethod "http://127.0.0.1:8000/health" -TimeoutSec 15
if ($Health.status -ne "healthy") { throw "Backend unhealthy after rollback." }
Write-Host "GL-04 rollback PASSED."
Write-Host "Restored source backup: $Backup"
