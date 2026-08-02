param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
& (Join-Path $Root "tools\social-credentials\verify.ps1") -Root $Root -Platform YouTube
$worker = Get-Content -LiteralPath (Join-Path $Root "tools\social-publishing\youtube-worker.ps1") -Raw
if ($worker -notmatch 'privacyStatus = "private"') { throw "Private-by-default guard is missing." }
if ($worker -match 'privacyStatus = "public"') { throw "Public publishing is forbidden in this milestone." }
Write-Host "P3-MVP-09 validation PASSED."
