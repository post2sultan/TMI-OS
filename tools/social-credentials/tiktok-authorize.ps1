param(
    [string]$Root = "O:\TMI-OS",
    [string]$RedirectUri = "http://127.0.0.1:53682/callback/",
    [int]$TimeoutSeconds = 300
)

$ErrorActionPreference = "Stop"
Import-Module (Join-Path $PSScriptRoot "SocialCredentialVault.psm1") -Force
$vaultPath = Join-Path $Root "docker\.env.social.vault.json"
Test-TmiSocialVault -Path $vaultPath -RequiredKeys @("TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET") | Out-Null
$vault = Get-Content -LiteralPath $vaultPath -Raw | ConvertFrom-Json
$clientKey = Unprotect-TmiSecret $vault.values.TIKTOK_CLIENT_KEY
$clientSecret = Unprotect-TmiSecret $vault.values.TIKTOK_CLIENT_SECRET

function New-RandomUrlSafeString([int]$ByteCount) {
    $bytes = New-Object byte[] $ByteCount
    [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    return [Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+', '-').Replace('/', '_')
}

$state = New-RandomUrlSafeString 24
$verifier = New-RandomUrlSafeString 48
$sha = [Security.Cryptography.SHA256]::Create()
try {
    $challengeBytes = $sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($verifier))
} finally {
    $sha.Dispose()
}
$challenge = -join ($challengeBytes | ForEach-Object { $_.ToString("x2") })
$scopes = "user.info.basic,video.upload"
$authorizeUri = "https://www.tiktok.com/v2/auth/authorize/?client_key=$([uri]::EscapeDataString($clientKey))&response_type=code&scope=$([uri]::EscapeDataString($scopes))&redirect_uri=$([uri]::EscapeDataString($RedirectUri))&state=$([uri]::EscapeDataString($state))&code_challenge=$challenge&code_challenge_method=S256"

$redirect = [uri]$RedirectUri
if ($redirect.Host -ne "127.0.0.1") { throw "TikTok redirect must use the 127.0.0.1 loopback address." }
$listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, $redirect.Port)
try {
    $listener.Start()
    Write-Host "Opening TikTok authorization. Approve access in the browser."
    Start-Process $authorizeUri
    $clientTask = $listener.AcceptTcpClientAsync()
    if (-not $clientTask.Wait([TimeSpan]::FromSeconds($TimeoutSeconds))) {
        throw "TikTok authorization timed out. Run the command again."
    }
    $client = $clientTask.Result
    $stream = $client.GetStream()
    $reader = [IO.StreamReader]::new($stream, [Text.Encoding]::ASCII, $false, 1024, $true)
    $requestLine = $reader.ReadLine()
    do { $headerLine = $reader.ReadLine() } while ($headerLine)
    $requestTarget = ($requestLine -split ' ')[1]
    if (-not $requestTarget) { throw "TikTok callback request was invalid." }
    Add-Type -AssemblyName System.Web
    $callbackUri = [uri]("http://127.0.0.1" + $requestTarget)
    $query = [Web.HttpUtility]::ParseQueryString($callbackUri.Query)
    $responseHtml = "<!doctype html><html><body><h2>TMI OS TikTok authorization received.</h2><p>You may close this tab and return to PowerShell.</p></body></html>"
    $responseBytes = [Text.Encoding]::UTF8.GetBytes($responseHtml)
    $responseHeader = [Text.Encoding]::ASCII.GetBytes("HTTP/1.1 200 OK`r`nContent-Type: text/html; charset=utf-8`r`nContent-Length: $($responseBytes.Length)`r`nConnection: close`r`n`r`n")
    $stream.Write($responseHeader, 0, $responseHeader.Length)
    $stream.Write($responseBytes, 0, $responseBytes.Length)
    $stream.Flush()
    $reader.Dispose()
    $stream.Dispose()
    $client.Close()
    if ($query["error"]) { throw "TikTok authorization failed: $($query['error'])" }
    if ($query["state"] -ne $state) { throw "TikTok OAuth state validation failed." }
    $code = $query["code"]
    if ([string]::IsNullOrWhiteSpace($code)) { throw "TikTok did not return an authorization code." }

    $token = Invoke-RestMethod -Method Post -Uri "https://open.tiktokapis.com/v2/oauth/token/" -ContentType "application/x-www-form-urlencoded" -Body @{
        client_key = $clientKey
        client_secret = $clientSecret
        code = $code
        grant_type = "authorization_code"
        redirect_uri = $RedirectUri
        code_verifier = $verifier
    }
    if (-not $token.access_token -or -not $token.refresh_token -or -not $token.open_id) {
        throw "TikTok token response was incomplete."
    }
    if ([string]$token.scope -notmatch "video.upload") { throw "TikTok video.upload permission was not granted." }
    $backup = "$vaultPath.$(Get-Date -Format 'yyyyMMdd-HHmmss').backup"
    Copy-Item -LiteralPath $vaultPath -Destination $backup -Force
    $now = [DateTimeOffset]::UtcNow
    $values = @{
        TIKTOK_ACCESS_TOKEN = ConvertTo-SecureString ([string]$token.access_token) -AsPlainText -Force
        TIKTOK_REFRESH_TOKEN = ConvertTo-SecureString ([string]$token.refresh_token) -AsPlainText -Force
        TIKTOK_OPEN_ID = ConvertTo-SecureString ([string]$token.open_id) -AsPlainText -Force
        TIKTOK_SCOPES = ConvertTo-SecureString ([string]$token.scope) -AsPlainText -Force
        TIKTOK_ACCESS_EXPIRES_AT = ConvertTo-SecureString ($now.AddSeconds([double]$token.expires_in).ToString("o")) -AsPlainText -Force
        TIKTOK_REFRESH_EXPIRES_AT = ConvertTo-SecureString ($now.AddSeconds([double]$token.refresh_expires_in).ToString("o")) -AsPlainText -Force
    }
    Update-TmiSocialVault -Values $values -Path $vaultPath
    Test-TmiSocialVault -Path $vaultPath -RequiredKeys @("TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_ACCESS_TOKEN", "TIKTOK_REFRESH_TOKEN", "TIKTOK_OPEN_ID") | Out-Null
    Write-Host "TikTok authorization PASSED. Tokens and creator ID encrypted locally."
} finally {
    $listener.Stop()
    $clientKey = $null
    $clientSecret = $null
    $code = $null
    $token = $null
    $verifier = $null
}
