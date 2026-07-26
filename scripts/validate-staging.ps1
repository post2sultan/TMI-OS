param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$Suffix = [Guid]::NewGuid().ToString("N").Substring(0, 12)
$TempRoot = Join-Path ([IO.Path]::GetTempPath()) "tmi-gl07-$Suffix"
$EnvFile = Join-Path $TempRoot "staging.env"
$BaseEnv = Join-Path $Root "docker\production.env.example"
$Compose = Join-Path $Root "docker\compose.production.yml"
$Overlay = Join-Path $Root "docker\compose.staging.yml"

New-Item -ItemType Directory -Force $TempRoot | Out-Null
try {
    & (Join-Path $Root "scripts\new-credential-bundle.ps1") `
        -SourceEnvFile $BaseEnv -OutputEnvFile $EnvFile
    $Content = Get-Content $EnvFile -Raw
    $Content = $Content.Replace("TMI_RELEASE_TAG=gl-06", "TMI_RELEASE_TAG=gl-07")
    [IO.File]::WriteAllText($EnvFile, $Content, [Text.UTF8Encoding]::new($false))

    docker compose --env-file $EnvFile -f $Compose -f $Overlay config --quiet
    if ($LASTEXITCODE -ne 0) { throw "Staging Compose validation failed." }
    & (Join-Path $Root "scripts\deploy-release.ps1") -Root $Root `
        -EnvFile $EnvFile -Environment staging -InitialDeployment

    $Health = Invoke-RestMethod "http://127.0.0.1:18000/health" -TimeoutSec 15
    $Ready = Invoke-RestMethod "http://127.0.0.1:18000/ready" -TimeoutSec 30
    $Web = Invoke-WebRequest "http://127.0.0.1:18080/healthz" -TimeoutSec 15
    $Metrics = (Invoke-WebRequest "http://127.0.0.1:18000/metrics" -TimeoutSec 15).Content
    $Prometheus = Invoke-RestMethod "http://127.0.0.1:19090/api/v1/rules" -TimeoutSec 15
    if ($Health.status -ne "healthy" -or $Ready.status -ne "ready") {
        throw "Staging API end-to-end check failed."
    }
    if ($Web.StatusCode -ne 200 -or $Metrics -notmatch "tmi_dependency_ready") {
        throw "Staging web or metrics check failed."
    }
    if ($Prometheus.status -ne "success") { throw "Staging alert rules unavailable." }
    Write-Host "GL-07 staging end-to-end validation PASSED."
}
finally {
    docker compose --env-file $EnvFile -f $Compose -f $Overlay down -v --remove-orphans
    if (Test-Path $TempRoot) { Remove-Item -Recurse -Force $TempRoot }
}
