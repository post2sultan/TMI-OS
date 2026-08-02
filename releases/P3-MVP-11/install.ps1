param([string]$Root="O:\TMI-OS")
& (Join-Path $Root "tools\social-credentials\verify.ps1") -Root $Root -Platform Instagram
if(-not(Test-Path "C:\Program Files (x86)\cloudflared\cloudflared.exe")){throw "cloudflared is not installed."}
Write-Host "P3-MVP-11 install preflight PASSED."
