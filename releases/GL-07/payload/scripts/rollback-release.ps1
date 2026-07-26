param(
    [string]$Root = "O:\TMI-OS",
    [Parameter(Mandatory = $true)][string]$EnvFile,
    [Parameter(Mandatory = $true)][string]$PreviousReleaseTag,
    [ValidateSet("staging", "production")][string]$Environment = "staging",
    [switch]$ApproveProduction
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
if ($Environment -eq "production" -and -not $ApproveProduction) {
    throw "Production rollback requires -ApproveProduction."
}
if ($PreviousReleaseTag -notmatch '^[a-z0-9][a-z0-9._-]{0,63}$') {
    throw "PreviousReleaseTag is invalid."
}
foreach ($Image in @("tmi-os-backend:$PreviousReleaseTag", "tmi-os-frontend:$PreviousReleaseTag")) {
    docker image inspect $Image | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Rollback image is unavailable: $Image" }
}

$Project = "tmi-$Environment"
$ComposeArgs = @("--env-file", ([IO.Path]::GetFullPath($EnvFile)), "--project-name", $Project,
    "-f", (Join-Path $Root "docker\compose.production.yml"))
if ($Environment -eq "staging") {
    $ComposeArgs += @("-f", (Join-Path $Root "docker\compose.staging.yml"))
}
$PreviousValue = $env:TMI_RELEASE_TAG
try {
    $env:TMI_RELEASE_TAG = $PreviousReleaseTag
    docker compose @ComposeArgs up -d --wait --no-build backend frontend
    if ($LASTEXITCODE -ne 0) { throw "Rollback deployment failed." }
}
finally {
    $env:TMI_RELEASE_TAG = $PreviousValue
}
Write-Host "$Environment rollback PASSED: $PreviousReleaseTag"
