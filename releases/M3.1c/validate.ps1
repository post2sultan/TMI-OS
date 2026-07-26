param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Frontend = Join-Path $Root "frontend"
$BaseUrl = "http://127.0.0.1:8000"
$PreviewUrl = "http://127.0.0.1:4173"
$PreviewProcess = $null

$Health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get -TimeoutSec 15
$Ready = Invoke-RestMethod -Uri "$BaseUrl/ready" -Method Get -TimeoutSec 15
$History = Invoke-RestMethod -Uri "$BaseUrl/discovery/history?limit=2&offset=0" -Method Get -TimeoutSec 15

if ($Health.status -ne "healthy") {
    throw "/health did not report healthy."
}

if ($Ready.status -ne "ready") {
    throw "/ready did not report ready."
}

if ($History.limit -ne 2 -or $History.offset -ne 0) {
    throw "Discovery-history pagination metadata is invalid."
}

foreach ($Item in $History.items) {
    foreach ($Field in @("id", "query", "provider", "status", "results_found", "credits_used", "duration_ms", "created_at")) {
        if ($null -eq $Item.PSObject.Properties[$Field]) {
            throw "Discovery-history item is missing field: $Field"
        }
    }
}

Push-Location $Frontend
try {
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend production build failed."
    }

    $PreviewProcess = Start-Process -FilePath "npm.cmd" `
        -ArgumentList @("run", "preview", "--", "--host", "127.0.0.1", "--port", "4173", "--strictPort") `
        -WindowStyle Hidden `
        -PassThru

    $Loaded = $false
    for ($Attempt = 1; $Attempt -le 30; $Attempt++) {
        try {
            $Page = Invoke-WebRequest -Uri $PreviewUrl -Method Get -TimeoutSec 5
            if ($Page.StatusCode -eq 200 -and $Page.Content -match 'id="root"') {
                $Loaded = $true
                break
            }
        }
        catch {
            Start-Sleep -Seconds 1
        }
    }

    if (-not $Loaded) {
        throw "Built frontend did not become available at $PreviewUrl."
    }
}
finally {
    if ($null -ne $PreviewProcess -and -not $PreviewProcess.HasExited) {
        Stop-Process -Id $PreviewProcess.Id -Force
    }
    Pop-Location
}

Write-Host ""
Write-Host "M3.1c validation PASSED."
Write-Host "Backend health:          $($Health.status)"
Write-Host "Backend readiness:       $($Ready.status)"
Write-Host "History records checked: $($History.items.Count)"
Write-Host "Frontend runtime:        HTTP 200"
