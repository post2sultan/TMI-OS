param([string]$Root="O:\TMI-OS", [string]$BaseUrl="http://127.0.0.1:5173", [switch]$Story)
$ErrorActionPreference="Stop"; Set-StrictMode -Version Latest
Import-Module (Join-Path $Root "tools\social-credentials\SocialCredentialVault.psm1") -Force
$vaultPath=Join-Path $Root "docker\.env.social.vault.json"
Test-TmiSocialVault -Path $vaultPath -RequiredKeys @("INSTAGRAM_ACCESS_TOKEN","INSTAGRAM_ACCOUNT_ID") | Out-Null
$vault=Get-Content $vaultPath -Raw | ConvertFrom-Json
$token=Unprotect-TmiSecret $vault.values.INSTAGRAM_ACCESS_TOKEN
$account=Unprotect-TmiSecret $vault.values.INSTAGRAM_ACCOUNT_ID
$envPath=Join-Path $Root "docker\.env.production.local"
$user=((Get-Content $envPath | Where-Object {$_ -match '^TMI_WEB_USER='}) -split '=',2)[1]
$pass=((Get-Content "$envPath.access.txt" | Where-Object {$_ -match '^One-time TMI web password:'}) -split ':',2)[1].Trim()
$basic=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("${user}:${pass}")); $localHeaders=@{Authorization="Basic $basic"}
$segment=if($Story){"instagram-story"}else{"instagram"}; $mediaType=if($Story){"STORIES"}else{"REELS"}
$job=Invoke-RestMethod "$BaseUrl/api/publishing/$segment/next" -Headers $localHeaders
if($job.status -eq "empty"){Write-Host "No Instagram publishing job is queued."; exit 0}
$temp=Join-Path ([IO.Path]::GetTempPath()) ("tmi-instagram-"+[guid]::NewGuid().ToString("N")); New-Item -ItemType Directory $temp | Out-Null
$fileName=([guid]::NewGuid().ToString("N")+".mp4"); $file=Join-Path $temp $fileName
$serverJob=$null; $tunnel=$null
function Report([string]$path,[hashtable]$body){Invoke-RestMethod -Method Post "$BaseUrl/api/publishing/$segment/$($job.job_id)/$path" -Headers $localHeaders -ContentType "application/json" -Body ($body|ConvertTo-Json -Compress)|Out-Null}
try {
  $sourceUrl=[string]$job.video_url
  if($Story){
    $source="/app/media/campaign-$($job.campaign_id)/video.mp4"; $story="/app/media/campaign-$($job.campaign_id)/instagram-story-59s.mp4"
    & docker exec tmi-production-backend-1 ffmpeg -y -i $source -t 59 -c:v libx264 -preset veryfast -crf 23 -c:a aac -b:a 128k -movflags +faststart $story 2>$null
    if($LASTEXITCODE -ne 0){throw "Could not create the Instagram Story duration-safe copy."}
    $sourceUrl="/api/media/campaign-$($job.campaign_id)/instagram-story-59s.mp4"
  }
  Invoke-WebRequest "$BaseUrl$sourceUrl" -Headers $localHeaders -OutFile $file
  if((Get-Item $file).Length -lt 10000){throw "Generated video is invalid."}
  $probe=[Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback,0); $probe.Start(); $port=([Net.IPEndPoint]$probe.LocalEndpoint).Port; $probe.Stop()
  $serverJob=Start-Job -ArgumentList $port,$fileName,$file -ScriptBlock {param($p,$name,$path); $l=[Net.HttpListener]::new(); $l.Prefixes.Add("http://127.0.0.1:$p/"); $l.Start(); try {while($true){$c=$l.GetContext(); if($c.Request.Url.AbsolutePath -ne "/$name"){$c.Response.StatusCode=404;$c.Response.Close();continue}; $bytes=[IO.File]::ReadAllBytes($path); $c.Response.ContentType="video/mp4";$c.Response.ContentLength64=$bytes.Length;$c.Response.OutputStream.Write($bytes,0,$bytes.Length);$c.Response.Close()}}finally{$l.Stop()}}
  $cloud="C:\Program Files (x86)\cloudflared\cloudflared.exe"; if(-not(Test-Path $cloud)){throw "cloudflared is unavailable."}
  $log=Join-Path $temp "tunnel.log"; $outLog=Join-Path $temp "tunnel-out.log"; $tunnel=Start-Process $cloud -ArgumentList @("tunnel","--url","http://127.0.0.1:$port","--no-autoupdate") -RedirectStandardError $log -RedirectStandardOutput $outLog -PassThru -WindowStyle Hidden
  $public=$null; for($i=0;$i -lt 30 -and -not $public;$i++){Start-Sleep 1; if(Test-Path $log){$m=[regex]::Match((Get-Content $log -Raw),'https://[a-z0-9-]+\.trycloudflare\.com'); if($m.Success){$public=$m.Value}}}; if(-not $public){throw "Temporary tunnel did not start."}
  $body=@{media_type=$mediaType;video_url="$public/$fileName";access_token=$token}; if(-not $Story){$body.caption=[string]$job.caption;$body.share_to_feed="true"}
  $container=Invoke-RestMethod -Method Post "https://graph.instagram.com/v24.0/$account/media" -Body $body
  if(-not $container.id){throw "Instagram did not create a Reel container."}
  $finished=$false; for($i=0;$i -lt 60 -and -not $finished;$i++){Start-Sleep 5; $state=Invoke-RestMethod "https://graph.instagram.com/v24.0/$($container.id)?fields=status_code&access_token=$([uri]::EscapeDataString($token))"; if($state.status_code -eq "FINISHED"){$finished=$true}; if($state.status_code -eq "ERROR"){throw "Instagram media processing failed."}}
  if(-not $finished){throw "Instagram media processing timed out."}
  $published=Invoke-RestMethod -Method Post "https://graph.instagram.com/v24.0/$account/media_publish" -Body @{creation_id=$container.id;access_token=$token}
  if(-not $published.id){throw "Instagram did not return a media ID."}; Report "complete" @{media_id=[string]$published.id}; Write-Host "Public Instagram $mediaType publishing PASSED for campaign $($job.campaign_id)."
} catch {try{Report "fail" @{error=$_.Exception.Message}}catch{}; throw} finally {if($tunnel -and -not $tunnel.HasExited){Stop-Process $tunnel.Id -Force}; if($serverJob){Stop-Job $serverJob -ErrorAction SilentlyContinue;Remove-Job $serverJob -Force -ErrorAction SilentlyContinue}; if(Test-Path $temp){Remove-Item $temp -Recurse -Force}; $token=$pass=$null}
