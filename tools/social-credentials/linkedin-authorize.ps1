param(
    [string]$Root = "O:\TMI-OS",
    [string]$RedirectUri = "http://127.0.0.1:53683/callback/",
    [int]$TimeoutSeconds = 300
)

$ErrorActionPreference = "Stop"
Import-Module (Join-Path $PSScriptRoot "SocialCredentialVault.psm1") -Force
$vaultPath = Join-Path $Root "docker\.env.social.vault.json"
Test-TmiSocialVault -Path $vaultPath -RequiredKeys @("LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET") | Out-Null
$vault = Get-Content -LiteralPath $vaultPath -Raw | ConvertFrom-Json
$clientId = Unprotect-TmiSecret $vault.values.LINKEDIN_CLIENT_ID
$clientSecret = Unprotect-TmiSecret $vault.values.LINKEDIN_CLIENT_SECRET

function New-RandomUrlSafeString([int]$ByteCount) {
    $bytes = New-Object byte[] $ByteCount
    $random = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $random.GetBytes($bytes) } finally { $random.Dispose() }
    return [Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+', '-').Replace('/', '_')
}

function Open-InBrave([string]$Uri) {
    $candidates = @(
        "C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        "C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
        (Join-Path $env:LOCALAPPDATA "BraveSoftware\Brave-Browser\Application\brave.exe")
    )
    $brave = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $brave) { throw "Brave browser was not found." }
    Start-Process -FilePath $brave -ArgumentList $Uri
}

$state = New-RandomUrlSafeString 24
$scopes = "openid profile w_member_social"
$authorizeUri = "https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=$([uri]::EscapeDataString($clientId))&redirect_uri=$([uri]::EscapeDataString($RedirectUri))&state=$([uri]::EscapeDataString($state))&scope=$([uri]::EscapeDataString($scopes))"

$redirect = [uri]$RedirectUri
if ($redirect.Host -ne "127.0.0.1") { throw "LinkedIn redirect must use the 127.0.0.1 loopback address." }
$listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, $redirect.Port)
try {
    $listener.Start()
    Write-Host "Opening LinkedIn authorization in Brave. Approve access in the browser."
    Open-InBrave $authorizeUri
    $clientTask = $listener.AcceptTcpClientAsync()
    if (-not $clientTask.Wait([TimeSpan]::FromSeconds($TimeoutSeconds))) {
        throw "LinkedIn authorization timed out. Run the command again."
    }
    $client = $clientTask.Result
    $stream = $client.GetStream()
    $reader = [IO.StreamReader]::new($stream, [Text.Encoding]::ASCII, $false, 1024, $true)
    $requestLine = $reader.ReadLine()
    do { $headerLine = $reader.ReadLine() } while ($headerLine)
    $requestTarget = ($requestLine -split ' ')[1]
    if (-not $requestTarget) { throw "LinkedIn callback request was invalid." }
    Add-Type -AssemblyName System.Web
    $callbackUri = [uri]("http://127.0.0.1" + $requestTarget)
    $query = [Web.HttpUtility]::ParseQueryString($callbackUri.Query)
    $responseHtml = "<!doctype html><html><body><h2>TMI OS LinkedIn authorization received.</h2><p>You may close this tab and return to PowerShell.</p></body></html>"
    $responseBytes = [Text.Encoding]::UTF8.GetBytes($responseHtml)
    $responseHeader = [Text.Encoding]::ASCII.GetBytes("HTTP/1.1 200 OK`r`nContent-Type: text/html; charset=utf-8`r`nContent-Length: $($responseBytes.Length)`r`nConnection: close`r`n`r`n")
    $stream.Write($responseHeader, 0, $responseHeader.Length)
    $stream.Write($responseBytes, 0, $responseBytes.Length)
    $stream.Flush()
    $reader.Dispose()
    $stream.Dispose()
    $client.Close()
    if ($query["error"]) { throw "LinkedIn authorization failed: $($query['error'])" }
    if ($query["state"] -ne $state) { throw "LinkedIn OAuth state validation failed." }
    $code = $query["code"]
    if ([string]::IsNullOrWhiteSpace($code)) { throw "LinkedIn did not return an authorization code." }

    $token = Invoke-RestMethod -Method Post -Uri "https://www.linkedin.com/oauth/v2/accessToken" -ContentType "application/x-www-form-urlencoded" -Body @{
        grant_type = "authorization_code"
        code = $code
        redirect_uri = $RedirectUri
        client_id = $clientId
        client_secret = $clientSecret
    }
    if (-not $token.access_token) { throw "LinkedIn token response was incomplete." }
    $profile = Invoke-RestMethod -Method Get -Uri "https://api.linkedin.com/v2/userinfo" -Headers @{ Authorization = "Bearer $($token.access_token)" }
    if (-not $profile.sub) { throw "LinkedIn did not return the authorized member identifier." }
    $authorUrn = "urn:li:person:$($profile.sub)"
    $backup = "$vaultPath.$(Get-Date -Format 'yyyyMMdd-HHmmss').backup"
    Copy-Item -LiteralPath $vaultPath -Destination $backup -Force
    $values = @{
        LINKEDIN_ACCESS_TOKEN = ConvertTo-SecureString ([string]$token.access_token) -AsPlainText -Force
        LINKEDIN_AUTHOR_URN = ConvertTo-SecureString $authorUrn -AsPlainText -Force
        LINKEDIN_SCOPES = ConvertTo-SecureString $scopes -AsPlainText -Force
        LINKEDIN_ACCESS_EXPIRES_AT = ConvertTo-SecureString ([DateTimeOffset]::UtcNow.AddSeconds([double]$token.expires_in).ToString("o")) -AsPlainText -Force
    }
    Update-TmiSocialVault -Values $values -Path $vaultPath
    Test-TmiSocialVault -Path $vaultPath -RequiredKeys @("LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET", "LINKEDIN_ACCESS_TOKEN", "LINKEDIN_AUTHOR_URN") | Out-Null
    Write-Host "LinkedIn authorization PASSED. Access token and member author encrypted locally."
} finally {
    $listener.Stop()
    $clientId = $null
    $clientSecret = $null
    $code = $null
    $token = $null
    $profile = $null
}
