param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$Release = Join-Path $Root "releases\GL-05"
$Reference = Join-Path $Release ".latest-backup.txt"
$Targets = @(
    ".github\workflows\supply-chain.yml",
    "backend\requirements.txt",
    "docker\production.env.example",
    "docs\GO_LIVE.md",
    "docs\SUPPLY_CHAIN.md",
    "frontend\package.json",
    "frontend\package-lock.json",
    "scripts\validate-supply-chain.ps1",
    "security\npm-audit-exceptions.json"
)
if (-not (Test-Path $Reference)) { throw "No GL-05 backup reference exists." }
$Backup = (Get-Content $Reference -Raw).Trim()
if (-not (Test-Path $Backup)) { throw "GL-05 backup not found: $Backup" }
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
Write-Host "GL-05 rollback PASSED."
Write-Host "Restored backup: $Backup"
