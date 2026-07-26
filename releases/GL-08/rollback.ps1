param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
$Release = Join-Path $Root "releases\GL-08"
$Reference = Join-Path $Release ".latest-backup.txt"
$Targets = @(
    ".github\workflows\supply-chain.yml", ".gitignore",
    "docker\production.env.example", "docs\GO_LIVE.md",
    "docs\LAUNCH_ACCEPTANCE.md", "scripts\validate-launch-rehearsal.ps1"
)
if (-not (Test-Path $Reference)) { throw "No GL-08 backup exists." }
$Backup = (Get-Content $Reference -Raw).Trim()
foreach ($Path in $Targets) {
    $Saved = Join-Path $Backup $Path; $Dest = Join-Path $Root $Path
    if (Test-Path $Saved) {
        New-Item -ItemType Directory -Force (Split-Path -Parent $Dest) | Out-Null
        Copy-Item -Force $Saved $Dest
    } elseif (Test-Path "$Saved.__missing__") {
        Remove-Item -Force -ErrorAction SilentlyContinue $Dest
    } else { throw "Backup entry missing: $Path" }
}
$Health = Invoke-RestMethod "http://127.0.0.1:8000/health" -TimeoutSec 15
if ($Health.status -ne "healthy") { throw "API unhealthy after rollback." }
Write-Host "GL-08 rollback PASSED."
