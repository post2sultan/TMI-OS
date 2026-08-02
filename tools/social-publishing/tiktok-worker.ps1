param([string]$Root="O:\TMI-OS", [string]$BaseUrl="http://127.0.0.1:5173")
$ErrorActionPreference="Stop"; Set-StrictMode -Version Latest
Import-Module (Join-Path $Root "tools\social-credentials\SocialCredentialVault.psm1") -Force
$vaultPath=Join-Path $Root "docker\.env.social.vault.json"
$required=@("TIKTOK_CLIENT_KEY","TIKTOK_CLIENT_SECRET","TIKTOK_ACCESS_TOKEN","TIKTOK_REFRESH_TOKEN","TIKTOK_OPEN_ID")
Test-TmiSocialVault -Path $vaultPath -RequiredKeys $required | Out-Null
$vault=Get-Content $vaultPath -Raw | ConvertFrom-Json
function Secret([string]$name){Unprotect-TmiSecret $vault.values.$name}
$envPath=Join-Path $Root "docker\.env.production.local"
$user=((Get-Content $envPath|Where-Object{$_ -match '^TMI_WEB_USER='})-split '=',2)[1]
$pass=((Get-Content "$envPath.access.txt"|Where-Object{$_ -match '^One-time TMI web password:'})-split ':',2)[1].Trim()
$basic=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("${user}:${pass}"));$localHeaders=@{Authorization="Basic $basic"}
$job=Invoke-RestMethod "$BaseUrl/api/publishing/tiktok/next" -Headers $localHeaders
if($job.status -eq "empty"){Write-Host "No TikTok draft upload is queued.";exit 0}
$temp=Join-Path ([IO.Path]::GetTempPath()) ("tmi-tiktok-"+[guid]::NewGuid().ToString("N")+".mp4")
function Report([string]$path,[hashtable]$body){Invoke-RestMethod -Method Post "$BaseUrl/api/publishing/tiktok/$($job.job_id)/$path" -Headers $localHeaders -ContentType "application/json" -Body ($body|ConvertTo-Json -Compress)|Out-Null}
try {
  Invoke-WebRequest "$BaseUrl$($job.video_url)" -Headers $localHeaders -OutFile $temp
  $size=(Get-Item $temp).Length;if($size -lt 10000){throw "Generated TikTok video is invalid."}
  $refresh=Invoke-RestMethod -Method Post "https://open.tiktokapis.com/v2/oauth/token/" -ContentType "application/x-www-form-urlencoded" -Body @{client_key=Secret "TIKTOK_CLIENT_KEY";client_secret=Secret "TIKTOK_CLIENT_SECRET";grant_type="refresh_token";refresh_token=Secret "TIKTOK_REFRESH_TOKEN"}
  if(-not $refresh.access_token -or -not $refresh.refresh_token){throw "TikTok token refresh failed."}
  $rotated=@{TIKTOK_ACCESS_TOKEN=ConvertTo-SecureString ([string]$refresh.access_token) -AsPlainText -Force;TIKTOK_REFRESH_TOKEN=ConvertTo-SecureString ([string]$refresh.refresh_token) -AsPlainText -Force}
  Update-TmiSocialVault -Values $rotated -Path $vaultPath
  $access=[string]$refresh.access_token
  $initBody=@{source_info=@{source="FILE_UPLOAD";video_size=$size;chunk_size=$size;total_chunk_count=1}}|ConvertTo-Json -Depth 4 -Compress
  $init=Invoke-RestMethod -Method Post "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/" -Headers @{Authorization="Bearer $access"} -ContentType "application/json; charset=UTF-8" -Body $initBody
  if($init.error.code -ne "ok" -or -not $init.data.upload_url -or -not $init.data.publish_id){throw "TikTok upload initialization failed: $($init.error.code) $($init.error.message)"}
  $last=$size-1
  Invoke-WebRequest -Method Put -Uri ([string]$init.data.upload_url) -Headers @{"Content-Range"="bytes 0-$last/$size";"Content-Length"="$size"} -ContentType "video/mp4" -InFile $temp | Out-Null
  Report "complete" @{publish_id=[string]$init.data.publish_id}
  Write-Host "TikTok draft upload PASSED for campaign $($job.campaign_id). Finish posting from TikTok Inbox."
} catch {try{Report "fail" @{error=$_.Exception.Message}}catch{};throw} finally {if(Test-Path $temp){Remove-Item $temp -Force};$access=$pass=$refresh=$rotated=$null}
