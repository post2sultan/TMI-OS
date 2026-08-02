param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
$module = Join-Path $Root "tools\social-credentials\SocialCredentialVault.psm1"
$authorize = Join-Path $Root "tools\social-credentials\linkedin-authorize.ps1"
foreach ($path in @($module, $authorize)) {
    $errors = $null
    [Management.Automation.Language.Parser]::ParseFile($path, [ref]$null, [ref]$errors) | Out-Null
    if ($errors.Count) { throw "PowerShell syntax validation failed: $path" }
}
$authorizeText = Get-Content -LiteralPath $authorize -Raw
if ($authorizeText -notmatch [regex]::Escape("/oauth/native-pkce/authorization")) {
    throw "LinkedIn helper is not using the native PKCE authorization endpoint."
}
$tokenBody = [regex]::Match($authorizeText, '(?s)accessToken.*?-Body @\{(?<body>.*?)\n\s*\}').Groups['body'].Value
if ($tokenBody -match 'client_secret') {
    throw "Native PKCE token exchange must not transmit the client secret."
}
Import-Module $module -Force
$testVault = Join-Path $Root "tmp\social-vault-08-self-test.json"
$existing = @{ TIKTOK_REFRESH_TOKEN = ConvertTo-SecureString "preserve-me" -AsPlainText -Force }
Update-TmiSocialVault -Values $existing -Path $testVault
$linkedin = @{}
foreach ($key in @("LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET", "LINKEDIN_ACCESS_TOKEN", "LINKEDIN_AUTHOR_URN")) {
    $linkedin[$key] = ConvertTo-SecureString "self-test-$key" -AsPlainText -Force
}
Update-TmiSocialVault -Values $linkedin -Path $testVault
Test-TmiSocialVault -Path $testVault -RequiredKeys @($linkedin.Keys) | Out-Null
$test = Get-Content -LiteralPath $testVault -Raw | ConvertFrom-Json
if ((Unprotect-TmiSecret $test.values.TIKTOK_REFRESH_TOKEN) -ne "preserve-me") { throw "Existing credentials were not preserved." }
Remove-Item -LiteralPath $testVault -Force
Write-Host "P3-MVP-08 validation PASSED. OAuth helper parses; LinkedIn fields encrypt; existing entries remain intact."
Write-Host "No real credentials or paid APIs used. Paid credits: 0"
