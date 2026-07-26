$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Get-ContainerEnvValue {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ContainerName,

        [Parameter(Mandatory = $true)]
        [string]$VariableName
    )

    $envLines = @(docker inspect --format "{{range .Config.Env}}{{println .}}{{end}}" $ContainerName 2>&1)

    if ($LASTEXITCODE -ne 0) {
        throw "Could not inspect container environment for $ContainerName.`n$($envLines -join [Environment]::NewLine)"
    }

    $prefix = "$VariableName="
    $match = $envLines | Where-Object { $_ -like "$prefix*" } | Select-Object -First 1

    if ([string]::IsNullOrWhiteSpace($match)) {
        throw "Environment variable $VariableName was not found in container $ContainerName."
    }

    return $match.Substring($prefix.Length)
}

function Get-DiscoveryRunCount {
    $dbUser = Get-ContainerEnvValue -ContainerName "tmi-postgres" -VariableName "POSTGRES_USER"
    $dbName = Get-ContainerEnvValue -ContainerName "tmi-postgres" -VariableName "POSTGRES_DB"

    $output = @(docker exec tmi-postgres psql `
        -U $dbUser `
        -d $dbName `
        -tA `
        -c "SELECT COUNT(*) FROM discovery_runs;" 2>&1)

    if ($LASTEXITCODE -ne 0) {
        throw "Could not read discovery_runs table.`n$($output -join [Environment]::NewLine)"
    }

    $value = ($output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Last 1)

    if ([string]::IsNullOrWhiteSpace($value)) {
        throw "The discovery_runs count query returned no value."
    }

    $parsed = 0
    if (-not [int]::TryParse($value.Trim(), [ref]$parsed)) {
        throw "Unexpected discovery_runs count returned: $value"
    }

    return $parsed
}

Write-Host "M3.1a - Validating..." -ForegroundColor Cyan

Write-Host "1/5 Checking containers..." -ForegroundColor Yellow
$running = @(docker ps --format "{{.Names}}")

foreach ($required in @("tmi-backend", "tmi-postgres")) {
    if ($running -notcontains $required) {
        throw "Required container is not running: $required"
    }
}

Write-Host "2/5 Checking health endpoints..." -ForegroundColor Yellow
Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 15 | Out-Null
Invoke-RestMethod -Uri "http://localhost:8000/ready" -Method Get -TimeoutSec 15 | Out-Null

Write-Host "3/5 Checking Python imports without bytecode..." -ForegroundColor Yellow
docker exec -e PYTHONDONTWRITEBYTECODE=1 tmi-backend python -B -c "from app.main import app; from app.repositories.discovery_run_repository import discovery_run_repository; print('IMPORT_OK')" | Out-Host

if ($LASTEXITCODE -ne 0) {
    throw "Python import validation failed."
}

Write-Host "4/5 Running real discovery request..." -ForegroundColor Yellow
$before = Get-DiscoveryRunCount

$body = @{
    prompt = "Saudi Arabia marketing campaigns"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://localhost:8000/discover" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body `
    -TimeoutSec 180 | Out-Null

Write-Host "5/5 Confirming DiscoveryRun persistence..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
$after = Get-DiscoveryRunCount

if ($after -le $before) {
    throw "Discovery request completed, but discovery_runs did not increase. Before=$before After=$after"
}

Write-Host ""
Write-Host "M3.1a validation PASSED." -ForegroundColor Green
Write-Host "DiscoveryRun rows before: $before" -ForegroundColor White
Write-Host "DiscoveryRun rows after:  $after" -ForegroundColor White
