param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
Import-Module (Join-Path $Root "tools\social-credentials\SocialCredentialVault.psm1") -Force
$TestVault = Join-Path $Root "tmp\social-vault-self-test.json"
$values = @{}
$keys = @("YOUTUBE_CLIENT_ID","YOUTUBE_CLIENT_SECRET","YOUTUBE_REFRESH_TOKEN","YOUTUBE_CHANNEL_ID","META_APP_ID","META_APP_SECRET","META_ACCESS_TOKEN","META_PAGE_ID","INSTAGRAM_ACCOUNT_ID","TIKTOK_CLIENT_KEY","TIKTOK_CLIENT_SECRET","TIKTOK_ACCESS_TOKEN","TIKTOK_OPEN_ID","LINKEDIN_CLIENT_ID","LINKEDIN_CLIENT_SECRET","LINKEDIN_ACCESS_TOKEN","LINKEDIN_AUTHOR_URN")
foreach ($key in $keys) { $values[$key] = ConvertTo-SecureString "self-test-$key" -AsPlainText -Force }
Save-TmiSocialVault -Values $values -Path $TestVault
Test-TmiSocialVault -Path $TestVault | Out-Null
Remove-Item -LiteralPath $TestVault -Force
git -C $Root check-ignore "docker/.env.social.vault.json" | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Vault is not Git-ignored." }
Write-Host "P3-MVP-05 validation PASSED."
Write-Host "No real credentials used. Paid API credits: 0"
