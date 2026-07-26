param(
    [string]$Root = "O:\TMI-OS",
    [int]$ProbePort = 18001
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ComposeFile = Join-Path $Root "docker\compose.production.yml"
$EnvFile = Join-Path $Root "docker\production.env.example"
$Network = "tmi-gl02-validation"
$DatabaseContainer = "tmi-gl02-probe-db"
$BackendContainer = "tmi-gl02-probe"
$Image = "tmi-os-backend:gl-02"
$DatabasePassword = "gl02-strong-postgres-secret"

$Rendered = docker compose --env-file $EnvFile -f $ComposeFile config --format json
if ($LASTEXITCODE -ne 0) { throw "Production Compose rendering failed." }
$Configuration = $Rendered | ConvertFrom-Json

foreach ($Name in @("postgres", "ollama", "qdrant", "redis", "searxng")) {
    $Service = $Configuration.services.$Name
    if ($Service.PSObject.Properties.Name -contains "ports") {
        throw "$Name exposes a host port."
    }
    if ($Service.image -match ":latest$") { throw "$Name uses a floating image." }
}

$Backend = $Configuration.services.backend
if (-not $Backend.read_only) { throw "Backend root filesystem is writable." }
if ($Backend.PSObject.Properties.Name -contains "volumes") {
    throw "Backend contains mutable source mounts."
}
if ($Backend.ports[0].host_ip -ne "127.0.0.1") {
    throw "Backend port is not bound to loopback."
}
if ($Backend.cap_drop -notcontains "ALL") {
    throw "Backend capabilities are not dropped."
}

docker compose --env-file $EnvFile -f $ComposeFile build backend
if ($LASTEXITCODE -ne 0) { throw "Production backend build failed." }
if ((docker image inspect $Image --format '{{.Config.User}}') -ne "tmi") {
    throw "Production image does not use the tmi account."
}

foreach ($Name in @($DatabaseContainer, $BackendContainer)) {
    if (docker ps -a --format '{{.Names}}' | Where-Object { $_ -eq $Name }) {
        throw "Validation container already exists: $Name"
    }
}
if (docker network ls --format '{{.Name}}' | Where-Object { $_ -eq $Network }) {
    throw "Validation network already exists: $Network"
}

docker network create $Network | Out-Null
try {
    docker run -d `
        --name $DatabaseContainer `
        --network $Network `
        --tmpfs /var/lib/postgresql/data `
        -e POSTGRES_DB=tmi_probe `
        -e POSTGRES_USER=tmi_probe `
        -e POSTGRES_PASSWORD=$DatabasePassword `
        postgres@sha256:de1e13ca94377fa5a27aafd0e9fc200df9692b15152f0090fdf074074ea5e397 |
        Out-Null

    $DatabaseReady = $false
    for ($Attempt = 1; $Attempt -le 30; $Attempt++) {
        docker exec $DatabaseContainer pg_isready -U tmi_probe -d tmi_probe |
            Out-Null
        if ($LASTEXITCODE -eq 0) {
            $DatabaseReady = $true
            break
        }
        Start-Sleep -Seconds 1
    }
    if (-not $DatabaseReady) { throw "Probe database did not become ready." }

    docker run -d `
        --name $BackendContainer `
        --network $Network `
        -p "127.0.0.1:$($ProbePort):8000" `
        --read-only `
        --tmpfs /tmp:size=64m,mode=1777 `
        --cap-drop ALL `
        --security-opt no-new-privileges `
        --pids-limit 256 `
        -e APP_ENV=production `
        -e POSTGRES_HOST=$DatabaseContainer `
        -e POSTGRES_DB=tmi_probe `
        -e POSTGRES_USER=tmi_probe `
        -e POSTGRES_PASSWORD=$DatabasePassword `
        -e AUTH_VIEWER_API_KEY=probe-viewer-secret `
        -e AUTH_OPERATOR_API_KEY=probe-operator-secret `
        -e AUTH_REVIEWER_API_KEY=probe-reviewer-secret `
        -e AUTH_ADMIN_API_KEY=probe-admin-secret `
        -e QDRANT_API_KEY=probe-qdrant-secret `
        -e REDIS_PASSWORD=probe-redis-secret `
        $Image |
        Out-Null

    $BaseUrl = "http://127.0.0.1:$ProbePort"
    $BackendReady = $false
    for ($Attempt = 1; $Attempt -le 30; $Attempt++) {
        try {
            $Ready = Invoke-RestMethod "$BaseUrl/ready" -TimeoutSec 3
            if ($Ready.status -eq "ready") {
                $BackendReady = $true
                break
            }
        }
        catch {
        }
        Start-Sleep -Seconds 1
    }
    if (-not $BackendReady) {
        docker logs $BackendContainer --tail 50
        throw "Production backend probe did not become ready."
    }

    try {
        Invoke-RestMethod "$BaseUrl/prompt" -TimeoutSec 5 | Out-Null
        throw "Anonymous production access was unexpectedly accepted."
    }
    catch {
        if ($_.Exception.Response.StatusCode.value__ -ne 401) { throw }
    }

    $Prompt = Invoke-RestMethod "$BaseUrl/prompt" -Headers @{
        "X-TMI-API-Key" = "probe-viewer-secret"
    } -TimeoutSec 5
    if (-not $Prompt.prompt) { throw "Authorized production request failed." }

    $Inspection = docker inspect $BackendContainer | ConvertFrom-Json
    if (-not $Inspection[0].HostConfig.ReadonlyRootfs) {
        throw "Runtime probe root filesystem is writable."
    }
    if ($Inspection[0].Config.User -ne "tmi") {
        throw "Runtime probe is not using the tmi account."
    }

    Write-Host "Production container validation PASSED."
}
finally {
    foreach ($Name in @($BackendContainer, $DatabaseContainer)) {
        if (docker ps -a --format '{{.Names}}' | Where-Object { $_ -eq $Name }) {
            docker rm -f $Name | Out-Null
        }
    }
    if (docker network ls --format '{{.Name}}' | Where-Object { $_ -eq $Network }) {
        docker network rm $Network | Out-Null
    }
}
