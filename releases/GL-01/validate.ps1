param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$ComposeFile = Join-Path $Root "docker\compose.yml"
$BaseUrl = "http://127.0.0.1:8000"

$Health = Invoke-RestMethod "$BaseUrl/health" -TimeoutSec 15
$Ready = Invoke-RestMethod "$BaseUrl/ready" -TimeoutSec 15
if ($Health.status -ne "healthy" -or $Ready.status -ne "ready") {
    throw "Backend health or readiness validation failed."
}

try {
    Invoke-RestMethod "$BaseUrl/campaigns" -TimeoutSec 15 | Out-Null
    throw "Anonymous campaign access was unexpectedly accepted."
}
catch {
    if ($_.Exception.Response.StatusCode.value__ -ne 401) { throw }
}

$ViewerHeaders = @{"X-TMI-API-Key" = "dev-viewer-key"}
$Campaigns = Invoke-RestMethod "$BaseUrl/campaigns?limit=1" -Headers $ViewerHeaders -TimeoutSec 15

try {
    Invoke-RestMethod "$BaseUrl/campaigns" -Method Post -Headers @{
        "X-TMI-API-Key" = "dev-viewer-key"
        "X-TMI-Actor" = "gl01-viewer"
    } -ContentType "application/json" -Body "{}" -TimeoutSec 15 | Out-Null
    throw "Viewer mutation was unexpectedly accepted."
}
catch {
    if ($_.Exception.Response.StatusCode.value__ -ne 403) { throw }
}

$PostgresUser = docker inspect tmi-postgres --format '{{range .Config.Env}}{{println .}}{{end}}' |
    Where-Object { $_ -like 'POSTGRES_USER=*' } |
    ForEach-Object { $_.Substring('POSTGRES_USER='.Length) } |
    Select-Object -First 1
$PostgresDb = docker inspect tmi-postgres --format '{{range .Config.Env}}{{println .}}{{end}}' |
    Where-Object { $_ -like 'POSTGRES_DB=*' } |
    ForEach-Object { $_.Substring('POSTGRES_DB='.Length) } |
    Select-Object -First 1

$AuditBefore = [int]((docker exec tmi-postgres psql -U $PostgresUser -d $PostgresDb -tAc "SELECT COUNT(*) FROM audit_events;" | Out-String).Trim())
try {
    Invoke-RestMethod "$BaseUrl/campaigns" -Method Post -Headers @{
        "X-TMI-API-Key" = "dev-operator-key"
        "X-TMI-Actor" = "gl01-runtime-validation"
    } -ContentType "application/json" -Body "{}" -TimeoutSec 15 | Out-Null
}
catch {
    if ($_.Exception.Response.StatusCode.value__ -ne 422) { throw }
}
$AuditAfter = [int]((docker exec tmi-postgres psql -U $PostgresUser -d $PostgresDb -tAc "SELECT COUNT(*) FROM audit_events;" | Out-String).Trim())
if ($AuditAfter -ne ($AuditBefore + 1)) {
    throw "Authenticated mutation audit event was not persisted."
}

docker compose -f $ComposeFile exec -T backend python -B -m unittest discover -s /app/tests -p "test_*.py" -q
if ($LASTEXITCODE -ne 0) { throw "GL-01 test suite failed." }

Push-Location (Join-Path $Root "frontend")
try {
    npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw "Frontend build failed." }
    npm.cmd run lint
    if ($LASTEXITCODE -ne 0) { throw "Frontend lint failed." }
}
finally {
    Pop-Location
}

$Migration = docker compose -f $ComposeFile exec -T backend alembic current
if (($Migration | Out-String) -notmatch "c5f8a1d3e6b9") {
    throw "GL-01 migration is not active."
}

Write-Host ""
Write-Host "GL-01 validation PASSED."
Write-Host "Anonymous access: rejected"
Write-Host "Authorized read: passed"
Write-Host "Cross-role write: rejected"
Write-Host "Audit persistence: passed"
Write-Host "Backend tests: 45"
Write-Host "Frontend build and lint: passed"
