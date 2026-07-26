param(
    [string]$Root = "O:\TMI-OS",
    [int]$ProbePort = 18080
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ComposeFile = Join-Path $Root "docker\compose.production.yml"
$EnvFile = Join-Path $Root "docker\production.env.example"
$Container = "tmi-gl03-probe"
$Image = "tmi-os-frontend:gl-03"
$Network = "tmi-platform_default"
$WebUser = "gl03-user"
$WebPassword = "gl03-password"
$ApiKey = "dev-admin-key"

$Rendered = docker compose --env-file $EnvFile -f $ComposeFile config --format json
if ($LASTEXITCODE -ne 0) { throw "Production Compose rendering failed." }
$Configuration = $Rendered | ConvertFrom-Json

foreach ($Property in $Configuration.services.PSObject.Properties) {
    $ServiceName = $Property.Name
    $Service = $Property.Value
    if ($ServiceName -ne "frontend" -and
        $Service.PSObject.Properties.Name -contains "ports") {
        throw "$ServiceName exposes a host port."
    }
}

$Frontend = $Configuration.services.frontend
$Backend = $Configuration.services.backend
if (-not $Frontend.read_only) { throw "Frontend root filesystem is writable." }
if ($Frontend.cap_drop -notcontains "ALL") {
    throw "Frontend capabilities are not dropped."
}
if ($Frontend.cap_add -notcontains "NET_BIND_SERVICE") {
    throw "Frontend cannot bind its service ports."
}
if ($Backend.PSObject.Properties.Name -contains "ports") {
    throw "Backend is publicly exposed."
}
if ($Backend.networks.PSObject.Properties.Name -contains "edge") {
    throw "Backend is attached to the public edge network."
}

docker compose --env-file $EnvFile -f $ComposeFile build frontend
if ($LASTEXITCODE -ne 0) { throw "Production frontend build failed." }

$SecretMatches = docker run --rm --entrypoint sh $Image -c "grep -R -l 'dev-admin-key' /srv 2>/dev/null || true"
if (($SecretMatches | Out-String).Trim()) {
    throw "A development API key was embedded in the production web bundle."
}

if (docker ps -a --format '{{.Names}}' | Where-Object { $_ -eq $Container }) {
    throw "Validation container already exists: $Container"
}
if (-not (docker network ls --format '{{.Name}}' | Where-Object { $_ -eq $Network })) {
    throw "Development backend network is unavailable: $Network"
}

$PasswordHash = (docker run --rm caddy:2-alpine caddy hash-password --plaintext $WebPassword | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or -not $PasswordHash) {
    throw "Could not generate the temporary web password hash."
}

try {
    docker run -d `
        --name $Container `
        --network $Network `
        -p "127.0.0.1:$($ProbePort):80" `
        --read-only `
        --tmpfs /tmp:size=32m,mode=1777 `
        --tmpfs /config:size=16m,mode=1777 `
        --tmpfs /data:size=16m,mode=1777 `
        --cap-drop ALL `
        --cap-add NET_BIND_SERVICE `
        --security-opt no-new-privileges `
        --pids-limit 128 `
        -e TMI_DOMAIN=http://127.0.0.1 `
        -e TMI_TLS_EMAIL=validation@example.invalid `
        -e TMI_WEB_USER=$WebUser `
        -e TMI_WEB_PASSWORD_HASH=$PasswordHash `
        -e AUTH_ADMIN_API_KEY=$ApiKey `
        $Image | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Frontend runtime probe failed to start." }

    $BaseUrl = "http://127.0.0.1:$ProbePort"
    $Ready = $false
    for ($Attempt = 1; $Attempt -le 30; $Attempt++) {
        try {
            $Health = Invoke-WebRequest "$BaseUrl/healthz" -UseBasicParsing -TimeoutSec 3
            if ($Health.StatusCode -eq 200) {
                $Ready = $true
                break
            }
        }
        catch {
        }
        Start-Sleep -Seconds 1
    }
    if (-not $Ready) {
        docker logs $Container --tail 50
        throw "Frontend runtime probe did not become ready."
    }

    try {
        Invoke-WebRequest "$BaseUrl/" -UseBasicParsing -TimeoutSec 5 | Out-Null
        throw "Anonymous web access was unexpectedly accepted."
    }
    catch {
        if ($_.Exception.Message -eq "Anonymous web access was unexpectedly accepted.") {
            throw
        }
        $StatusCode = [int]$_.Exception.Response.StatusCode
        if ($StatusCode -ne 401) { throw }
    }

    $Credential = [Convert]::ToBase64String(
        [Text.Encoding]::ASCII.GetBytes("$($WebUser):$($WebPassword)")
    )
    $Headers = @{ Authorization = "Basic $Credential" }
    $WebResponse = Invoke-WebRequest "$BaseUrl/" -Headers $Headers -UseBasicParsing -TimeoutSec 5
    if ($WebResponse.StatusCode -ne 200 -or $WebResponse.Content -notmatch '<div id="root">') {
        throw "Authenticated frontend request failed."
    }

    $RequiredHeaders = @{
        "Strict-Transport-Security" = "max-age=31536000; includeSubDomains"
        "X-Content-Type-Options" = "nosniff"
        "X-Frame-Options" = "DENY"
        "Referrer-Policy" = "strict-origin-when-cross-origin"
        "Permissions-Policy" = "camera=(), microphone=(), geolocation=()"
        "Content-Security-Policy" = "default-src 'self'"
    }
    foreach ($Header in $RequiredHeaders.GetEnumerator()) {
        $Value = [string]$WebResponse.Headers[$Header.Key]
        if ($Value -notlike "*$($Header.Value)*") {
            throw "Missing or invalid security header: $($Header.Key)"
        }
    }

    $ApiResponse = Invoke-RestMethod "$BaseUrl/api/campaigns?limit=1" `
        -Headers $Headers -TimeoutSec 10
    if ($null -eq $ApiResponse) {
        throw "Same-origin API proxy returned no response."
    }

    $Inspection = docker inspect $Container | ConvertFrom-Json
    if (-not $Inspection[0].HostConfig.ReadonlyRootfs) {
        throw "Frontend runtime root filesystem is writable."
    }

    Write-Host "Production web entry validation PASSED."
}
finally {
    if (docker ps -a --format '{{.Names}}' | Where-Object { $_ -eq $Container }) {
        docker rm -f $Container | Out-Null
    }
}
