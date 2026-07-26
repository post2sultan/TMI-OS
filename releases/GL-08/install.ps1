param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$Release = Join-Path $Root "releases\GL-08"
$Payload = Join-Path $Release "payload"
$Backup = Join-Path (Join-Path $Release "backups") (Get-Date -Format "yyyyMMdd-HHmmss")
$Reference = Join-Path $Release ".latest-backup.txt"
$Targets = @(
    ".github\workflows\supply-chain.yml", ".gitignore",
    "docker\production.env.example", "docs\GO_LIVE.md",
    "docs\LAUNCH_ACCEPTANCE.md", "scripts\validate-launch-rehearsal.ps1"
)
function Restore-Backup {
    foreach ($Path in $Targets) {
        $Saved = Join-Path $Backup $Path; $Dest = Join-Path $Root $Path
        if (Test-Path $Saved) {
            New-Item -ItemType Directory -Force (Split-Path -Parent $Dest) | Out-Null
            Copy-Item -Force $Saved $Dest
        } elseif (Test-Path "$Saved.__missing__") {
            Remove-Item -Force -ErrorAction SilentlyContinue $Dest
        }
    }
}
try {
    if (-not (Test-Path $Payload)) {
        foreach ($Path in $Targets) {
            $Source = Join-Path $Root $Path; $Dest = Join-Path $Payload $Path
            New-Item -ItemType Directory -Force (Split-Path -Parent $Dest) | Out-Null
            Copy-Item -Force $Source $Dest
        }
    }
    foreach ($Path in $Targets) {
        $Saved = Join-Path $Backup $Path
        New-Item -ItemType Directory -Force (Split-Path -Parent $Saved) | Out-Null
        $GitPath = $Path.Replace("\", "/")
        if ((git -C $Root ls-tree --name-only HEAD -- $GitPath | Out-String).Trim()) {
            [IO.File]::WriteAllLines($Saved, (git -C $Root show "HEAD:$GitPath"))
        } else { New-Item -ItemType File -Force "$Saved.__missing__" | Out-Null }
    }
    Set-Content $Reference $Backup -Encoding UTF8
    foreach ($Path in $Targets) {
        $Dest = Join-Path $Root $Path
        New-Item -ItemType Directory -Force (Split-Path -Parent $Dest) | Out-Null
        Copy-Item -Force (Join-Path $Payload $Path) $Dest
    }
    & (Join-Path $Release "validate.ps1") -Root $Root
    Write-Host "GL-08 installation PASSED. Backup: $Backup"
} catch { Restore-Backup; throw }
