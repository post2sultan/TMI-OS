param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ComposeFile = Join-Path $Root "docker\compose.yml"
$BaseUrl = "http://127.0.0.1:8000"

function Invoke-Api {
    param(
        [Parameter(Mandatory = $true)][string]$Url
    )

    return Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 15
}

$Health = Invoke-Api -Url "$BaseUrl/health"
$Ready = Invoke-Api -Url "$BaseUrl/ready"
$FirstPage = Invoke-Api -Url "$BaseUrl/discovery/history?limit=2&offset=0"
$SecondPage = Invoke-Api -Url "$BaseUrl/discovery/history?limit=1&offset=1"

if ($Health.status -ne "healthy") {
    throw "/health did not report healthy."
}

if ($Ready.status -ne "ready") {
    throw "/ready did not report ready."
}

if ($FirstPage.limit -ne 2 -or $FirstPage.offset -ne 0) {
    throw "First-page pagination metadata is invalid."
}

if ($SecondPage.limit -ne 1 -or $SecondPage.offset -ne 1) {
    throw "Second-page pagination metadata is invalid."
}

$PostgresUser = docker inspect tmi-postgres --format '{{range .Config.Env}}{{println .}}{{end}}' |
    Where-Object { $_ -like 'POSTGRES_USER=*' } |
    ForEach-Object { $_.Substring('POSTGRES_USER='.Length) } |
    Select-Object -First 1

$PostgresDb = docker inspect tmi-postgres --format '{{range .Config.Env}}{{println .}}{{end}}' |
    Where-Object { $_ -like 'POSTGRES_DB=*' } |
    ForEach-Object { $_.Substring('POSTGRES_DB='.Length) } |
    Select-Object -First 1

if (-not $PostgresUser) {
    throw "Could not resolve POSTGRES_USER from tmi-postgres."
}

if (-not $PostgresDb) {
    throw "Could not resolve POSTGRES_DB from tmi-postgres."
}

$DatabaseCountRaw = docker exec tmi-postgres psql `
    -U $PostgresUser `
    -d $PostgresDb `
    -tAc "SELECT COUNT(*) FROM discovery_runs;"

if ($LASTEXITCODE -ne 0) {
    throw "Database count query failed."
}

$DatabaseCountText = ($DatabaseCountRaw | Out-String).Trim()
$DatabaseCount = 0

if (-not [int]::TryParse($DatabaseCountText, [ref]$DatabaseCount)) {
    throw "Database count was not numeric: $DatabaseCountText"
}

if ([int]$FirstPage.total -ne $DatabaseCount) {
    throw "API total ($($FirstPage.total)) does not match database count ($DatabaseCount)."
}

if ($FirstPage.items.Count -gt 1) {
    $FirstId = [int]$FirstPage.items[0].id
    $SecondId = [int]$FirstPage.items[1].id

    if ($FirstId -lt $SecondId) {
        throw "Discovery history is not newest-first."
    }
}

if ($DatabaseCount -gt 1 -and $SecondPage.items.Count -eq 1 -and $FirstPage.items.Count -gt 1) {
    if ([int]$SecondPage.items[0].id -ne [int]$FirstPage.items[1].id) {
        throw "Offset pagination returned an unexpected record."
    }
}

Write-Host ""
Write-Host "M3.1b validation PASSED."
Write-Host "DiscoveryRun database rows: $DatabaseCount"
Write-Host "API total:                  $($FirstPage.total)"
Write-Host "First page items:           $($FirstPage.items.Count)"