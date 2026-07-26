param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$Release = Join-Path $Root "releases\GL-07"
$Reference = Join-Path $Release ".latest-backup.txt"
$Targets = @(
    ".github\workflows\supply-chain.yml",
    "docker\compose.production.yml",
    "docker\compose.staging.yml",
    "docker\production.env.example",
    "docs\CREDENTIAL_ROTATION.md",
    "docs\GO_LIVE.md",
    "docs\INCIDENT_RESPONSE.md",
    "docs\OPERATIONS.md",
    "scripts\deploy-release.ps1",
    "scripts\new-credential-bundle.ps1",
    "scripts\rollback-release.ps1",
    "scripts\validate-operations.ps1",
    "scripts\validate-staging.ps1"
)
if (-not (Test-Path $Reference)) { throw "No GL-07 backup reference exists." }
$Backup = (Get-Content $Reference -Raw).Trim()
if (-not (Test-Path $Backup)) { throw "GL-07 backup not found: $Backup" }
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
    else { throw "Backup entry missing: $RelativePath" }
}
$Health = Invoke-RestMethod "http://127.0.0.1:8000/health" -TimeoutSec 15
if ($Health.status -ne "healthy") { throw "Development API unhealthy after rollback." }
Write-Host "GL-07 rollback PASSED."
