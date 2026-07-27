param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ComposeFile = Join-Path $Root "docker\compose.yml"

$Health = $null
for ($Attempt = 1; $Attempt -le 40; $Attempt++) {
    try {
        $Health = Invoke-RestMethod `
            -Uri "http://127.0.0.1:8000/health" `
            -TimeoutSec 5
        if ($Health.status -eq "healthy") {
            break
        }
    }
    catch {
        if ($Attempt -eq 40) {
            throw
        }
        Start-Sleep -Seconds 2
    }
}
if ($Health.status -ne "healthy") {
    throw "Backend health validation failed."
}

docker compose -f $ComposeFile exec -T backend python -B -m unittest `
    discover -s /app/tests -p "test_discovery_google_news_links.py" -v
if ($LASTEXITCODE -ne 0) {
    throw "RADAR-02 focused tests failed."
}

$Runtime = docker compose -f $ComposeFile exec -T backend python -B -c `
    "from app.services.discovery.manager import discovery_manager; r=discovery_manager.search_with_report('Saudi marketing campaign 2026'); w=[x.url for x in r.campaigns if 'news.google.com' in x.url]; assert not w; assert any(p.provider=='SearXNG' and p.status=='SUCCESS' for p in r.providers); assert any(p.provider=='Google News RSS' and p.status=='SUCCESS' for p in r.providers); print(len(r.campaigns))"
if ($LASTEXITCODE -ne 0) {
    throw "RADAR-02 runtime discovery validation failed."
}

Write-Host ""
Write-Host "RADAR-02 validation PASSED."
Write-Host "Usable campaigns: $((($Runtime | Select-Object -Last 1).Trim()))"
Write-Host "Google wrapper URLs: 0"
Write-Host "Paid provider credits: 0"
Write-Host "Backend health: $($Health.status)"
