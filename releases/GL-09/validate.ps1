param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$script = Join-Path $Root "releases\GL-09\validate_runtime.py"
docker cp $script tmi-production-backend-1:/tmp/gl09_validate.py
if ($LASTEXITCODE -ne 0) { throw "Runtime validator copy failed." }
$result = docker exec tmi-production-backend-1 python /tmp/gl09_validate.py
if (
    $LASTEXITCODE -ne 0 -or
    $result -notmatch "DISCOVERY_ANALYSIS_REVIEW_APPROVED_PUBLISHED_LOGGED_PASSED"
) {
    throw "GL-09 lifecycle runtime validation failed."
}
Write-Host "GL-09 lifecycle validation PASSED."
Write-Host "Paid API credits: 0"
