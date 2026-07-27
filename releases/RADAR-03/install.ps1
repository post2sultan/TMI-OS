param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\RADAR-03"
$Backup = Join-Path $Release "backups\$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$LatestBackupFile = Join-Path $Release ".latest-backup.txt"
$TargetRelative = "frontend/src/pages/CampaignRadarPage.tsx"
$Target = Join-Path $Root $TargetRelative
$Stored = Join-Path $Backup $TargetRelative
$ComposeFile = Join-Path $Root "docker\compose.production.yml"
$EnvFile = Join-Path $Root "docker\.env.production.local"
$ComposeArgs = @(
    "--env-file", $EnvFile,
    "--project-name", "tmi-production",
    "-f", $ComposeFile
)

function Restore-Backup {
    if (Test-Path $Stored) {
        Copy-Item -Force $Stored $Target
    }
}

try {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Stored) | Out-Null
    $Committed = git -C $Root show "HEAD:$TargetRelative"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not capture the committed Campaign Radar page."
    }
    Set-Content -LiteralPath $Stored -Value $Committed -Encoding utf8
    Set-Content -LiteralPath $LatestBackupFile -Value $Backup -Encoding utf8

    docker compose @ComposeArgs config --quiet
    if ($LASTEXITCODE -ne 0) {
        throw "Production compose configuration is invalid."
    }

    docker compose @ComposeArgs build frontend
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend image build failed."
    }

    docker compose @ComposeArgs up -d --no-deps --wait frontend
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend deployment failed."
    }

    & (Join-Path $Release "validate.ps1") -Root $Root

    Write-Host ""
    Write-Host "RADAR-03 installation PASSED."
    Write-Host "Backup: $Backup"
}
catch {
    Write-Host ""
    Write-Host "RADAR-03 installation FAILED. Rolling back..." -ForegroundColor Red
    Restore-Backup
    try {
        docker compose @ComposeArgs build frontend | Out-Null
        docker compose @ComposeArgs up -d --no-deps --wait frontend | Out-Null
    }
    catch {
    }
    throw
}
