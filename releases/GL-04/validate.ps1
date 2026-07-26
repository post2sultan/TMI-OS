param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$DataTestRoot = Join-Path $Root ".gl04-validation"
$LatestDataBackup = Get-ChildItem $DataTestRoot -Directory |
    Where-Object Name -match '^\d{8}T\d{6}Z$' |
    Sort-Object Name -Descending | Select-Object -First 1
if (-not $LatestDataBackup) { throw "No GL-04 validation backup exists." }

& (Join-Path $Root "scripts\validate-data-restore.ps1") `
    -BackupPath $LatestDataBackup.FullName -RtoTargetMinutes 30

$Health = Invoke-RestMethod "http://127.0.0.1:8000/health" -TimeoutSec 15
$Ready = Invoke-RestMethod "http://127.0.0.1:8000/ready" -TimeoutSec 15
if ($Health.status -ne "healthy" -or $Ready.status -ne "ready") {
    throw "Development stack health validation failed."
}
docker compose -f (Join-Path $Root "docker\compose.yml") exec -T backend `
    python -B -m unittest discover -s /app/tests -p "test_*.py" -q
if ($LASTEXITCODE -ne 0) { throw "Backend regression tests failed." }

Write-Host "GL-04 validation PASSED."
Write-Host "RPO target: 24 hours"
Write-Host "RTO target: 30 minutes"
Write-Host "PostgreSQL isolated restore: passed"
Write-Host "Qdrant isolated restore: passed"
Write-Host "Checksums and retention contract: passed"
