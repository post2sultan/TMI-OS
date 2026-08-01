param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
$module = Join-Path $Root "tools\social-credentials\SocialCredentialVault.psm1"
$authorize = Join-Path $Root "tools\social-credentials\tiktok-authorize.ps1"
foreach ($path in @($module, $authorize)) {
    $errors = $null
    [Management.Automation.Language.Parser]::ParseFile($path, [ref]$null, [ref]$errors) | Out-Null
    if ($errors.Count) { throw "PowerShell syntax validation failed: $path" }
}
Import-Module $module -Force
$testVault = Join-Path $Root "tmp\social-vault-07-self-test.json"
$existing = @{ INSTAGRAM_ACCESS_TOKEN = ConvertTo-SecureString "preserve-me" -AsPlainText -Force }
Update-TmiSocialVault -Values $existing -Path $testVault
$tiktok = @{}
foreach ($key in @("TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_ACCESS_TOKEN", "TIKTOK_REFRESH_TOKEN", "TIKTOK_OPEN_ID")) {
    $tiktok[$key] = ConvertTo-SecureString "self-test-$key" -AsPlainText -Force
}
Update-TmiSocialVault -Values $tiktok -Path $testVault
Test-TmiSocialVault -Path $testVault -RequiredKeys @($tiktok.Keys) | Out-Null
$test = Get-Content -LiteralPath $testVault -Raw | ConvertFrom-Json
if ((Unprotect-TmiSecret $test.values.INSTAGRAM_ACCESS_TOKEN) -ne "preserve-me") { throw "Existing credentials were not preserved." }
Remove-Item -LiteralPath $testVault -Force
Write-Host "P3-MVP-07 validation PASSED. OAuth helper parses; TikTok token fields encrypt; existing entries remain intact."
Write-Host "No real credentials or paid APIs used. Paid credits: 0"
