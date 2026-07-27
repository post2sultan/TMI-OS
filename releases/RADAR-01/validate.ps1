param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ComposeFile = Join-Path $Root "docker\compose.yml"
$RuntimeSettings = Join-Path $Root "data\searxng\settings.yml"
$Deadline = (Get-Date).AddSeconds(90)
$Payload = $null

if (-not (Test-Path $RuntimeSettings)) {
    throw "SearXNG runtime settings are missing."
}

$SettingsText = Get-Content -LiteralPath $RuntimeSettings -Raw
if ($SettingsText -notmatch '(?ms)formats:\s*.*-\s*json') {
    throw "SearXNG JSON output is not enabled."
}
if ($SettingsText -match 'secret_key:\s*["'']?ultrasecretkey') {
    throw "SearXNG still uses the template secret."
}

while ((Get-Date) -lt $Deadline) {
    try {
        $Payload = Invoke-RestMethod `
            -Uri "http://127.0.0.1:8080/search?q=Saudi%20campaign&format=json" `
            -TimeoutSec 15
        if ($Payload.results.Count -gt 0) {
            break
        }
    }
    catch {
        Start-Sleep -Seconds 2
    }
}

if ($null -eq $Payload -or $Payload.results.Count -lt 1) {
    throw "SearXNG JSON search returned no results."
}

$ProviderCheck = docker compose -f $ComposeFile exec -T backend python -B -c `
    "from app.services.discovery.providers.searxng import searxng_provider; r=searxng_provider.search('Saudi campaign', 3); assert len(r)>0; print(len(r))"
if ($LASTEXITCODE -ne 0 -or [int](($ProviderCheck | Select-Object -Last 1).Trim()) -lt 1) {
    throw "Backend SearXNG provider validation failed."
}

$Health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 15
if ($Health.status -ne "healthy") {
    throw "Backend health validation failed."
}

Write-Host ""
Write-Host "RADAR-01 validation PASSED."
Write-Host "Direct SearXNG results: $($Payload.results.Count)"
Write-Host "Backend provider results: $((($ProviderCheck | Select-Object -Last 1).Trim()))"
Write-Host "Backend health: $($Health.status)"
