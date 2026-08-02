param([string]$Root="O:\TMI-OS",[string]$BaseUrl="http://127.0.0.1:5173")
$ErrorActionPreference="Stop";Set-StrictMode -Version Latest
Import-Module (Join-Path $Root "tools\social-credentials\SocialCredentialVault.psm1") -Force
$vaultPath=Join-Path $Root "docker\.env.social.vault.json";$required=@("LINKEDIN_ACCESS_TOKEN","LINKEDIN_AUTHOR_URN")
Test-TmiSocialVault -Path $vaultPath -RequiredKeys $required|Out-Null;$vault=Get-Content $vaultPath -Raw|ConvertFrom-Json
function Secret([string]$name){Unprotect-TmiSecret $vault.values.$name}
$configuredAuthor=Secret "LINKEDIN_AUTHOR_URN"
if($configuredAuthor -notlike "urn:li:organization:*"){throw "LinkedIn publishing is blocked: an organization Page author URN is required."}
$envPath=Join-Path $Root "docker\.env.production.local";$user=((Get-Content $envPath|Where-Object{$_ -match '^TMI_WEB_USER='})-split '=',2)[1]
$pass=((Get-Content "$envPath.access.txt"|Where-Object{$_ -match '^One-time TMI web password:'})-split ':',2)[1].Trim();$basic=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("${user}:${pass}"));$localHeaders=@{Authorization="Basic $basic"}
$job=Invoke-RestMethod "$BaseUrl/api/publishing/linkedin/next" -Headers $localHeaders;if($job.status -eq "empty"){Write-Host "No LinkedIn publish job is queued.";exit 0}
$temp=Join-Path ([IO.Path]::GetTempPath()) ("tmi-linkedin-"+[guid]::NewGuid().ToString("N"));New-Item -ItemType Directory $temp|Out-Null
function Report([string]$path,[hashtable]$body){Invoke-RestMethod -Method Post "$BaseUrl/api/publishing/linkedin/$($job.job_id)/$path" -Headers $localHeaders -ContentType "application/json" -Body ($body|ConvertTo-Json -Compress)|Out-Null}
try {
  $zip=Join-Path $temp "social.zip";Invoke-WebRequest "$BaseUrl$($job.social_export_url)" -Headers $localHeaders -OutFile $zip;Expand-Archive $zip -DestinationPath $temp -Force
  $video=Join-Path $temp "linkedin\post.mp4";$size=(Get-Item $video).Length;if($size -lt 10000){throw "LinkedIn video is invalid."}
  $token=Secret "LINKEDIN_ACCESS_TOKEN";$author=$configuredAuthor;$apiHeaders=@{Authorization="Bearer $token";"LinkedIn-Version"="202607";"X-Restli-Protocol-Version"="2.0.0"}
  $initBody=@{initializeUploadRequest=@{owner=$author;fileSizeBytes=$size;uploadCaptions=$false;uploadThumbnail=$false}}|ConvertTo-Json -Depth 5 -Compress
  $init=Invoke-RestMethod -Method Post 'https://api.linkedin.com/rest/videos?action=initializeUpload' -Headers $apiHeaders -ContentType 'application/json' -Body $initBody
  $instructions=@($init.value.uploadInstructions);if($instructions.Count -ne 1){throw "LinkedIn MVP requires a single-part video upload."};$videoUrn=[string]$init.value.video;if(-not $videoUrn){throw "LinkedIn did not return a video URN."}
  $upload=Invoke-WebRequest -Method Put -Uri ([string]$instructions[0].uploadUrl) -ContentType 'application/octet-stream' -InFile $video
  $etag=[string]$upload.Headers['ETag'];if(-not $etag){throw "LinkedIn did not return an uploaded part ID."};$etag=$etag.Trim('"')
  $finalBody=@{finalizeUploadRequest=@{video=$videoUrn;uploadToken=[string]$init.value.uploadToken;uploadedPartIds=@($etag)}}|ConvertTo-Json -Depth 5 -Compress
  Invoke-RestMethod -Method Post 'https://api.linkedin.com/rest/videos?action=finalizeUpload' -Headers $apiHeaders -ContentType 'application/json' -Body $finalBody|Out-Null
  $encoded=[uri]::EscapeDataString($videoUrn);$available=$false;for($i=0;$i -lt 60 -and -not $available;$i++){Start-Sleep 5;$state=Invoke-RestMethod "https://api.linkedin.com/rest/videos/$encoded" -Headers $apiHeaders;if($state.status -eq 'AVAILABLE'){$available=$true};if($state.status -eq 'PROCESSING_FAILED'){throw "LinkedIn video processing failed."}};if(-not $available){throw "LinkedIn video processing timed out."}
  $postBody=@{author=$author;commentary=[string]$job.commentary;visibility="PUBLIC";distribution=@{feedDistribution="MAIN_FEED";targetEntities=@();thirdPartyDistributionChannels=@()};content=@{media=@{id=$videoUrn;title=[string]$job.title}};lifecycleState="PUBLISHED";isReshareDisabledByAuthor=$false}|ConvertTo-Json -Depth 7 -Compress
  $post=Invoke-WebRequest -Method Post 'https://api.linkedin.com/rest/posts' -Headers $apiHeaders -ContentType 'application/json' -Body $postBody;$postUrn=[string]$post.Headers['x-restli-id'];if(-not $postUrn){throw "LinkedIn did not return a post URN."}
  Report "complete" @{post_urn=$postUrn;video_urn=$videoUrn};Write-Host "Public LinkedIn video publishing PASSED for campaign $($job.campaign_id)."
}catch{try{Report "fail" @{error=$_.Exception.Message}}catch{};throw}finally{if(Test-Path $temp){Remove-Item $temp -Recurse -Force};$token=$pass=$null}
