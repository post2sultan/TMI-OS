param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
Import-Module (Join-Path $Root "tools\social-credentials\SocialCredentialVault.psm1") -Force
$testVault = Join-Path $Root "tmp\social-vault-05a-self-test.json"
$first = @{ YOUTUBE_CLIENT_ID = ConvertTo-SecureString "preserve-me" -AsPlainText -Force }
Update-TmiSocialVault -Values $first -Path $testVault
$instagram = @{}
foreach ($key in @("INSTAGRAM_APP_ID", "INSTAGRAM_APP_SECRET", "INSTAGRAM_ACCESS_TOKEN")) {
    $instagram[$key] = ConvertTo-SecureString "self-test-$key" -AsPlainText -Force
}
Update-TmiSocialVault -Values $instagram -Path $testVault
Test-TmiSocialVault -Path $testVault -RequiredKeys @("YOUTUBE_CLIENT_ID", "INSTAGRAM_APP_ID", "INSTAGRAM_APP_SECRET", "INSTAGRAM_ACCESS_TOKEN") | Out-Null
$vault = Get-Content -LiteralPath $testVault -Raw | ConvertFrom-Json
if ($vault.version -ne 2) { throw "Vault schema was not upgraded to version 2." }
if ((Unprotect-TmiSecret $vault.values.YOUTUBE_CLIENT_ID) -ne "preserve-me") { throw "Existing credential was not preserved." }
Remove-Item -LiteralPath $testVault -Force
git -C $Root check-ignore "docker/.env.social.vault.json" | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Vault is not Git-ignored." }
git -C $Root check-ignore "docker/.env.social.vault.json.20000101-000000.backup" | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Timestamped vault backups are not Git-ignored." }
Write-Host "P3-MVP-05A validation PASSED. Existing entries preserved; Instagram fields decrypt successfully."
Write-Host "No real credentials used. Paid API credits: 0"
