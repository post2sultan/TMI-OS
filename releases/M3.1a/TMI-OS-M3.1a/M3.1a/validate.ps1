param(
    [string]$ProjectRoot = "O:\TMI-OS",
    [string]$ApiBaseUrl = "http://localhost:8000"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ComposeFile = Join-Path $ProjectRoot "docker\compose.yml"

Write-Host "M3.1a - Validating..."

if (-not (Test-Path $ComposeFile)) {
    throw "Docker Compose file not found: $ComposeFile"
}

& docker compose -f $ComposeFile ps --status running backend | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Backend container is not running."
}

& docker compose -f $ComposeFile exec -T backend python -m compileall -q /app/app
if ($LASTEXITCODE -ne 0) {
    throw "Backend Python compilation failed."
}

$PythonValidation = @'
from uuid import uuid4

from sqlalchemy import delete, select

from app.core.database import SessionLocal
from app.models.discovery_run import DiscoveryRun
from app.repositories.discovery_run_repository import discovery_run_repository
from app.services.discovery.manager import ProviderExecution

query = f"m3.1a-validation-{uuid4()}"
database = SessionLocal()

try:
    ids = discovery_run_repository.persist_report(
        database=database,
        query=query,
        providers=[
            ProviderExecution(
                provider="validation-provider",
                status="SUCCESS",
                results=3,
                duration_ms=125,
            )
        ],
    )

    if len(ids) != 1:
        raise RuntimeError(f"Expected one persisted run, received {ids}")

    run = database.scalar(
        select(DiscoveryRun).where(DiscoveryRun.id == ids[0])
    )

    if run is None:
        raise RuntimeError("Persisted DiscoveryRun could not be read back")

    if run.query != query:
        raise RuntimeError("Persisted query does not match")

    if run.provider != "validation-provider":
        raise RuntimeError("Persisted provider does not match")

    if run.results_found != 3 or run.duration_ms != 125:
        raise RuntimeError("Persisted execution metrics do not match")

    database.execute(delete(DiscoveryRun).where(DiscoveryRun.id == run.id))
    database.commit()
    print("DiscoveryRun persistence: PASS")
finally:
    database.close()
'@

$PythonValidation | & docker compose -f $ComposeFile exec -T backend python -
if ($LASTEXITCODE -ne 0) {
    throw "DiscoveryRun persistence validation failed."
}

$Health = Invoke-RestMethod -Method Get -Uri "$ApiBaseUrl/health" -TimeoutSec 20
if ($Health.status -ne "healthy") {
    throw "Health endpoint did not return healthy status."
}

$Ready = Invoke-RestMethod -Method Get -Uri "$ApiBaseUrl/ready" -TimeoutSec 20
if ($Ready.status -ne "ready") {
    throw "Readiness endpoint did not return ready status."
}

Write-Host ""
Write-Host "M3.1a validation PASSED." -ForegroundColor Green
