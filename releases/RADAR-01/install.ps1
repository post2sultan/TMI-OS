param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\RADAR-01"
$Template = Join-Path $Release "payload\settings.yml"
$RuntimeSettings = Join-Path $Root "data\searxng\settings.yml"
$BackupRoot = Join-Path $Release "backups"
$Backup = Join-Path $BackupRoot (Get-Date -Format "yyyyMMdd-HHmmss")
$LatestBackupFile = Join-Path $Release ".latest-backup.txt"
$ComposeFile = Join-Path $Root "docker\compose.yml"

function Restore-Settings {
    $BackupSettings = Join-Path $Backup "settings.yml"
    if (Test-Path $BackupSettings) {
        Copy-Item -Force $BackupSettings $RuntimeSettings
    }
    elseif (Test-Path (Join-Path $Backup "settings.yml.__missing__")) {
        Remove-Item -Force -ErrorAction SilentlyContinue $RuntimeSettings
    }
}

try {
    if (-not (Test-Path $Template)) {
        throw "RADAR-01 settings template is missing."
    }

    New-Item -ItemType Directory -Force -Path $Backup | Out-Null
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $RuntimeSettings) | Out-Null

    if (Test-Path $RuntimeSettings) {
        Copy-Item -Force $RuntimeSettings (Join-Path $Backup "settings.yml")
        $Existing = Get-Content -LiteralPath $RuntimeSettings -Raw
        $SecretMatch = [regex]::Match(
            $Existing,
            '(?m)^\s*secret_key:\s*["'']?([^"''#\r\n]+)'
        )
        if (-not $SecretMatch.Success) {
            throw "Existing SearXNG secret could not be preserved."
        }
        $Secret = $SecretMatch.Groups[1].Value.Trim()
    }
    else {
        New-Item -ItemType File -Path (Join-Path $Backup "settings.yml.__missing__") | Out-Null
        $Bytes = New-Object byte[] 32
        [Security.Cryptography.RandomNumberGenerator]::Fill($Bytes)
        $Secret = [Convert]::ToHexString($Bytes).ToLowerInvariant()
    }

    if (-not $Secret -or $Secret -eq "ultrasecretkey") {
        throw "A non-placeholder SearXNG secret is required."
    }

    $Rendered = (Get-Content -LiteralPath $Template -Raw).Replace(
        "ultrasecretkey",
        $Secret
    )
    Set-Content -LiteralPath $RuntimeSettings -Value $Rendered -Encoding utf8
    Set-Content -LiteralPath $LatestBackupFile -Value $Backup -Encoding utf8

    docker compose -f $ComposeFile up -d --force-recreate searxng
    if ($LASTEXITCODE -ne 0) {
        throw "SearXNG could not be restarted."
    }

    & (Join-Path $Release "validate.ps1") -Root $Root

    Write-Host ""
    Write-Host "RADAR-01 installation PASSED."
    Write-Host "Backup: $Backup"
}
catch {
    Write-Host ""
    Write-Host "RADAR-01 installation FAILED. Rolling back..." -ForegroundColor Red
    Restore-Settings
    try {
        docker compose -f $ComposeFile up -d --force-recreate searxng | Out-Null
    }
    catch {
    }
    throw
}
