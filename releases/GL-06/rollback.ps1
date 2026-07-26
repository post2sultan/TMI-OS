param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\GL-06"
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

if (-not (Test-Path $Reference)) { throw "No GL-06 backup reference exists." }
$Backup = (Get-Content $Reference -Raw).Trim()
if (-not (Test-Path $Backup)) { throw "GL-06 backup not found: $Backup" }

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
    else {
        throw "Backup entry missing for: $RelativePath"
    }
}

docker compose -f (Join-Path $Root "docker\compose.yml") restart backend
if ($LASTEXITCODE -ne 0) { throw "Backend restart failed after rollback." }
$Health = $null
for ($Attempt = 1; $Attempt -le 15; $Attempt++) {
    try {
        $Health = Invoke-RestMethod "http://127.0.0.1:8000/health" -TimeoutSec 5
        if ($Health.status -eq "healthy") { break }
    }
    catch {
        if ($Attempt -eq 15) { throw }
        Start-Sleep -Seconds 1
    }
}
if ($null -eq $Health -or $Health.status -ne "healthy") {
    throw "Backend unhealthy after rollback."
}

Write-Host "GL-06 rollback PASSED."
Write-Host "Restored backup: $Backup"
