param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Import-Module (Join-Path $PSScriptRoot "SocialCredentialVault.psm1") -Force
$Vault = Join-Path $Root "docker\.env.social.vault.json"
$fields = [ordered]@{
    YOUTUBE_CLIENT_ID = "YouTube OAuth client ID"
    YOUTUBE_CLIENT_SECRET = "YouTube OAuth client secret"
    YOUTUBE_REFRESH_TOKEN = "YouTube OAuth refresh token"
    YOUTUBE_CHANNEL_ID = "YouTube channel ID"
    META_APP_ID = "Meta app ID"
    META_APP_SECRET = "Meta app secret"
    META_ACCESS_TOKEN = "Meta long-lived access token"
    META_PAGE_ID = "Facebook Page ID linked to Instagram"
    INSTAGRAM_ACCOUNT_ID = "Instagram professional account ID"
    TIKTOK_CLIENT_KEY = "TikTok client key"
    TIKTOK_CLIENT_SECRET = "TikTok client secret"
    TIKTOK_ACCESS_TOKEN = "TikTok access token"
    TIKTOK_OPEN_ID = "TikTok creator open ID"
    LINKEDIN_CLIENT_ID = "LinkedIn client ID"
    LINKEDIN_CLIENT_SECRET = "LinkedIn client secret"
    LINKEDIN_ACCESS_TOKEN = "LinkedIn access token"
    LINKEDIN_AUTHOR_URN = "LinkedIn person or organization URN"
}

Write-Host "TMI OS private social credential setup"
Write-Host "Values are hidden, encrypted for this Windows account, and never committed."
$values = @{}
foreach ($entry in $fields.GetEnumerator()) {
    do {
        $value = Read-Host $entry.Value -AsSecureString
        $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($value)
        try { $empty = [string]::IsNullOrWhiteSpace([Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)) }
        finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
    } while ($empty)
    $values[$entry.Key] = $value
}
if (Test-Path -LiteralPath $Vault) {
    Copy-Item -LiteralPath $Vault -Destination "$Vault.backup" -Force
}
Save-TmiSocialVault -Values $values -Path $Vault
Test-TmiSocialVault -Path $Vault | Out-Null
$values.Clear()
Write-Host "Social credentials encrypted and validated locally."
