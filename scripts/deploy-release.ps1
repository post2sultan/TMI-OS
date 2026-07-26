param(
    [string]$Root = "O:\TMI-OS",
    [Parameter(Mandatory = $true)][string]$EnvFile,
    [ValidateSet("staging", "production")][string]$Environment = "staging",
    [switch]$ApproveProduction,
    [switch]$InitialDeployment,
    [string]$OffsiteBackupRoot = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ($Environment -eq "production" -and -not $ApproveProduction) {
    throw "Production deployment requires -ApproveProduction."
}
$EnvFile = [IO.Path]::GetFullPath($EnvFile)
$EnvText = Get-Content $EnvFile -Raw
if ($EnvText -match "REPLACE_WITH_|ChangeThisPassword|dev-(viewer|operator|reviewer|admin)") {
    throw "Deployment environment contains placeholder or development secrets."
}

$Files = @((Join-Path $Root "docker\compose.production.yml"))
$Project = "tmi-production"
if ($Environment -eq "staging") {
    $Files += (Join-Path $Root "docker\compose.staging.yml")
    $Project = "tmi-staging"
}
$ComposeArgs = @("--env-file", $EnvFile, "--project-name", $Project)
foreach ($File in $Files) { $ComposeArgs += @("-f", $File) }

docker compose @ComposeArgs config --quiet
if ($LASTEXITCODE -ne 0) { throw "Deployment configuration is invalid." }

$Existing = docker compose @ComposeArgs ps -q postgres
if (($Existing | Out-String).Trim() -and -not $InitialDeployment) {
    $BackupRoot = Join-Path $Root "deployment-backups\$Environment"
    & (Join-Path $Root "scripts\backup-data.ps1") -Root $Root `
        -OutputRoot $BackupRoot -OffsiteRoot $OffsiteBackupRoot `
        -PostgresContainer "$Project-postgres-1" `
        -QdrantContainer "$Project-qdrant-1" `
        -BackendContainer "$Project-backend-1"
}

docker compose @ComposeArgs build backend frontend
if ($LASTEXITCODE -ne 0) { throw "Release image build failed." }
docker compose @ComposeArgs up -d --wait --remove-orphans
if ($LASTEXITCODE -ne 0) { throw "Deployment did not become healthy." }

$ApiPort = if ($Environment -eq "staging") { 18000 } else { 8000 }
if ($Environment -eq "staging") {
    $Ready = Invoke-RestMethod "http://127.0.0.1:$ApiPort/ready" -TimeoutSec 30
    if ($Ready.status -ne "ready") { throw "Staging readiness check failed." }
}

Write-Host "$Environment deployment PASSED."
Write-Host "Project: $Project"
