param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$Release = Join-Path $Root "releases\GL-07"
$Payload = Join-Path $Release "payload"
$Backup = Join-Path (Join-Path $Release "backups") (Get-Date -Format "yyyyMMdd-HHmmss")
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

function Restore-Backup {
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
        $Saved = Join-Path $Backup $RelativePath
        New-Item -ItemType Directory -Force (Split-Path -Parent $Saved) | Out-Null
        $GitPath = $RelativePath.Replace("\", "/")
        $Tracked = git -C $Root ls-tree --name-only HEAD -- $GitPath
        if (($Tracked | Out-String).Trim()) {
            [IO.File]::WriteAllLines($Saved, (git -C $Root show "HEAD:$GitPath"))
        }
        else { New-Item -ItemType File -Force "$Saved.__missing__" | Out-Null }
    }
    Set-Content $Reference $Backup -Encoding UTF8
    foreach ($RelativePath in $Targets) {
        $Source = Join-Path $Payload $RelativePath
        $Destination = Join-Path $Root $RelativePath
        New-Item -ItemType Directory -Force (Split-Path -Parent $Destination) | Out-Null
        Copy-Item -Force $Source $Destination
    }
    & (Join-Path $Root "releases\GL-07\validate.ps1") -Root $Root
    Write-Host "GL-07 installation PASSED."
    Write-Host "Backup: $Backup"
}
catch {
    Restore-Backup
    throw
}
