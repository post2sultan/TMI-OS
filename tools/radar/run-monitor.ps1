param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [string]$EnvFile = "O:\TMI-OS\docker\.env.production.local",
    [switch]$Force
)
$ErrorActionPreference = "Stop"
$line = Get-Content -LiteralPath $EnvFile | Where-Object { $_ -match '^AUTH_ADMIN_API_KEY=' } | Select-Object -First 1
if (-not $line) { throw "AUTH_ADMIN_API_KEY is missing from the private production environment file." }
$apiKey = $line.Substring($line.IndexOf('=') + 1).Trim().Trim('"')
$headers = @{ "X-TMI-API-Key" = $apiKey; "X-TMI-Actor" = "RADAR-06-Monitor" }
$body = @{ force = [bool]$Force } | ConvertTo-Json
$result = Invoke-RestMethod -Method Post -Uri "$BaseUrl/radar/monitor/run" -Headers $headers -ContentType "application/json" -Body $body
$result | ConvertTo-Json -Depth 6
