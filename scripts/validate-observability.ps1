param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ComposeFile = Join-Path $Root "docker\compose.production.yml"
$EnvFile = Join-Path $Root "docker\production.env.example"
$PrometheusConfig = Join-Path $Root "monitoring\prometheus.yml"
$AlertRules = Join-Path $Root "monitoring\alerts.yml"
$BlackboxConfig = Join-Path $Root "monitoring\blackbox.yml"

docker compose --env-file $EnvFile -f $ComposeFile config --quiet
if ($LASTEXITCODE -ne 0) { throw "Production Compose configuration is invalid." }

docker run --rm --entrypoint promtool `
    -v "${PrometheusConfig}:/etc/prometheus/prometheus.yml:ro" `
    -v "${AlertRules}:/etc/prometheus/alerts.yml:ro" `
    prom/prometheus@sha256:8672a850efe2f9874702406c8318704edb363587f8c2ca88586b4c8fdb5cea24 `
    check config /etc/prometheus/prometheus.yml
if ($LASTEXITCODE -ne 0) { throw "Prometheus configuration validation failed." }

$Rendered = docker compose --env-file $EnvFile -f $ComposeFile config
if ($LASTEXITCODE -ne 0) { throw "Production Compose rendering failed." }
$RenderedText = $Rendered | Out-String
foreach ($Required in @(
    "prom/prometheus@sha256:",
    "prom/blackbox-exporter@sha256:",
    "read_only: true",
    "cap_drop:",
    "${BlackboxConfig}"
)) {
    if ($RenderedText -notmatch [regex]::Escape($Required)) {
        throw "Production monitoring contract missing: $Required"
    }
}
if ($RenderedText -match "(?m)^\s+ports:\s*$[\s\S]{0,150}9090:") {
    throw "Prometheus must not publish a host port."
}

$RequestId = "gl06-runtime-$([guid]::NewGuid().ToString('N'))"
$Health = Invoke-WebRequest "http://127.0.0.1:8000/health" `
    -Headers @{ "X-Request-ID" = $RequestId } -TimeoutSec 15
if ($Health.StatusCode -ne 200) { throw "Backend liveness check failed." }
if ($Health.Headers["X-Request-ID"] -ne $RequestId) {
    throw "Request correlation header validation failed."
}

try {
    $ReadyResponse = Invoke-WebRequest "http://127.0.0.1:8000/ready" `
        -TimeoutSec 30
}
catch {
    $ReadyResponse = $_.Exception.Response
    throw "Dependency readiness failed with HTTP $($ReadyResponse.StatusCode)."
}
$Readiness = $ReadyResponse.Content | ConvertFrom-Json
foreach ($Dependency in @("postgres", "qdrant", "redis", "searxng", "ollama")) {
    if ($Readiness.dependencies.$Dependency -ne $true) {
        throw "Dependency is not ready: $Dependency"
    }
}

$Metrics = (Invoke-WebRequest "http://127.0.0.1:8000/metrics" `
    -TimeoutSec 15).Content
foreach ($Metric in @(
    "tmi_http_requests_total",
    "tmi_http_request_duration_seconds_total",
    "tmi_dependency_ready"
)) {
    if ($Metrics -notmatch $Metric) { throw "Metric missing: $Metric" }
}

$PreviousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$Logs = docker logs tmi-backend --since 2m 2>&1 | Out-String
$ErrorActionPreference = $PreviousErrorActionPreference
if ($Logs -notmatch [regex]::Escape($RequestId)) {
    throw "Structured logs do not contain the runtime request ID."
}
Write-Host "GL-06 observability validation PASSED."
Write-Host "Dependencies: PostgreSQL, Qdrant, Redis, SearXNG, Ollama ready"
Write-Host "Correlation, structured logs, metrics, alerts, uptime probes: passed"
