param(
    [string]$Root = "O:\TMI-OS",
    [ValidateSet("YouTube", "Instagram", "TikTok", "LinkedIn")]
    [string]$Platform
)

$ErrorActionPreference = "Stop"
Import-Module (Join-Path $PSScriptRoot "SocialCredentialVault.psm1") -Force
$Vault = Join-Path $Root "docker\.env.social.vault.json"
$platformFields = @{
    YouTube = [ordered]@{
        YOUTUBE_CLIENT_ID = "YouTube OAuth client ID"
        YOUTUBE_CLIENT_SECRET = "YouTube OAuth client secret"
        YOUTUBE_REFRESH_TOKEN = "YouTube OAuth refresh token"
        YOUTUBE_CHANNEL_ID = "YouTube channel ID"
    }
    Instagram = [ordered]@{
        INSTAGRAM_APP_ID = "Instagram app ID"
        INSTAGRAM_APP_SECRET = "Instagram app secret"
        INSTAGRAM_ACCESS_TOKEN = "Instagram access token"
    }
    TikTok = [ordered]@{
        TIKTOK_CLIENT_KEY = "TikTok client key"
        TIKTOK_CLIENT_SECRET = "TikTok client secret"
        TIKTOK_ACCESS_TOKEN = "TikTok access token"
        TIKTOK_OPEN_ID = "TikTok creator open ID"
    }
    LinkedIn = [ordered]@{
        LINKEDIN_CLIENT_ID = "LinkedIn client ID"
        LINKEDIN_CLIENT_SECRET = "LinkedIn client secret"
        LINKEDIN_ACCESS_TOKEN = "LinkedIn access token"
        LINKEDIN_AUTHOR_URN = "LinkedIn person or organization URN"
    }
}

if (-not $Platform) {
    $Platform = Read-Host "Platform to configure (YouTube, Instagram, TikTok, LinkedIn)"
    if (-not $platformFields.ContainsKey($Platform)) { throw "Unsupported platform: $Platform" }
}
$fields = $platformFields[$Platform]

Write-Host "TMI OS private $Platform credential setup"
Write-Host "Values are hidden, encrypted for this Windows account, and existing credentials are preserved."
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
    $backup = "$Vault.$(Get-Date -Format 'yyyyMMdd-HHmmss').backup"
    Copy-Item -LiteralPath $Vault -Destination $backup -Force
}
Update-TmiSocialVault -Values $values -Path $Vault
Test-TmiSocialVault -Path $Vault -RequiredKeys @($fields.Keys) | Out-Null
$values.Clear()
Write-Host "$Platform credentials encrypted and validated locally."
