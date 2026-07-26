param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\GL-05"
$Patch = Join-Path $Release "patch"
$Backup = Join-Path (Join-Path $Release "backups") (Get-Date -Format "yyyyMMdd-HHmmss")
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
    Set-Content $Reference $Backup -Encoding UTF8
    foreach ($RelativePath in $Targets) {
        $Source = Join-Path $Patch $RelativePath
        $Destination = Join-Path $Root $RelativePath
        New-Item -ItemType Directory -Force (Split-Path -Parent $Destination) | Out-Null
        Copy-Item -Force $Source $Destination
    }

    Push-Location (Join-Path $Root "frontend")
    try {
        npm install
        if ($LASTEXITCODE -ne 0) { throw "Frontend dependency synchronization failed." }
        npm run lint
        if ($LASTEXITCODE -ne 0) { throw "Frontend lint failed." }
        npm run build
        if ($LASTEXITCODE -ne 0) { throw "Frontend build failed." }
    }
    finally { Pop-Location }

    & (Join-Path $Root "scripts\validate-supply-chain.ps1") -Root $Root
    Write-Host "GL-05 installation PASSED."
    Write-Host "Backup: $Backup"
}
catch {
    Write-Host "GL-05 installation FAILED. Rolling back..." -ForegroundColor Red
    Restore-SourceBackup
    throw
}
