param(
    [string]$Root = "O:\TMI-OS",
    [string]$BaseUrl = "http://127.0.0.1:5173",
    [switch]$Watch,
    [int]$PollSeconds = 10
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
Import-Module (Join-Path $Root "tools\social-credentials\SocialCredentialVault.psm1") -Force
$vaultPath = Join-Path $Root "docker\.env.social.vault.json"
$required = @("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN", "YOUTUBE_CHANNEL_ID")
Test-TmiSocialVault -Path $vaultPath -RequiredKeys $required | Out-Null
$vault = Get-Content -LiteralPath $vaultPath -Raw | ConvertFrom-Json

function Secret([string]$Name) { Unprotect-TmiSecret $vault.values.$Name }

function Send-Result([int]$JobId, [string]$Path, [hashtable]$Body) {
    Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/publishing/youtube/$JobId/$Path" `
        -ContentType "application/json" -Body ($Body | ConvertTo-Json -Compress) | Out-Null
}

function Invoke-YouTubeJob {
    $job = Invoke-RestMethod -Uri "$BaseUrl/api/publishing/youtube/next"
    if ($job.status -eq "empty") { return $false }
    $temp = Join-Path ([IO.Path]::GetTempPath()) ("tmi-youtube-{0}-{1}.mp4" -f $job.job_id, [guid]::NewGuid().ToString("N"))
    try {
        Invoke-WebRequest -Uri "$BaseUrl$($job.video_url)" -OutFile $temp
        if ((Get-Item -LiteralPath $temp).Length -lt 10000) { throw "Generated video file is invalid." }
        $token = Invoke-RestMethod -Method Post -Uri "https://oauth2.googleapis.com/token" -ContentType "application/x-www-form-urlencoded" -Body @{
            client_id = Secret "YOUTUBE_CLIENT_ID"
            client_secret = Secret "YOUTUBE_CLIENT_SECRET"
            refresh_token = Secret "YOUTUBE_REFRESH_TOKEN"
            grant_type = "refresh_token"
        }
        $metadata = @{
            snippet = @{ title = [string]$job.title; description = [string]$job.description; categoryId = "22" }
            status = @{ privacyStatus = "private"; selfDeclaredMadeForKids = $false }
        } | ConvertTo-Json -Depth 5 -Compress
        $headers = @{
            Authorization = "Bearer $($token.access_token)"
            "X-Upload-Content-Length" = (Get-Item -LiteralPath $temp).Length
            "X-Upload-Content-Type" = "video/mp4"
        }
        $session = Invoke-WebRequest -Method Post -Uri "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status" `
            -Headers $headers -ContentType "application/json; charset=UTF-8" -Body $metadata
        $upload = Invoke-RestMethod -Method Put -Uri $session.Headers.Location -ContentType "video/mp4" -InFile $temp
        if (-not $upload.id) { throw "YouTube did not return a video ID." }
        Send-Result $job.job_id "complete" @{ video_id = [string]$upload.id }
        Write-Host "Private YouTube upload PASSED for campaign $($job.campaign_id)."
    }
    catch {
        $message = $_.Exception.Message
        try { Send-Result $job.job_id "fail" @{ error = $message } } catch { }
        throw
    }
    finally {
        if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Force }
        $token = $null
    }
    return $true
}

do {
    $worked = Invoke-YouTubeJob
    if ($Watch -and -not $worked) { Start-Sleep -Seconds $PollSeconds }
} while ($Watch)
