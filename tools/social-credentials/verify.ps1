param(
    [string]$Root = "O:\TMI-OS",
    [ValidateSet("YouTube", "Instagram", "TikTok", "LinkedIn")]
    [string]$Platform
)
$ErrorActionPreference = "Stop"
Import-Module (Join-Path $PSScriptRoot "SocialCredentialVault.psm1") -Force
$required = @{
    YouTube = @("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN", "YOUTUBE_CHANNEL_ID")
    Instagram = @("INSTAGRAM_APP_ID", "INSTAGRAM_APP_SECRET", "INSTAGRAM_ACCESS_TOKEN")
    TikTok = @("TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_ACCESS_TOKEN", "TIKTOK_OPEN_ID")
    LinkedIn = @("LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET", "LINKEDIN_ACCESS_TOKEN", "LINKEDIN_AUTHOR_URN")
}
if (-not $Platform) { throw "Specify -Platform YouTube, Instagram, TikTok, or LinkedIn." }
Test-TmiSocialVault -Path (Join-Path $Root "docker\.env.social.vault.json") -RequiredKeys $required[$Platform] | Out-Null
Write-Host "Credential vault structure and Windows decryption PASSED."
Write-Host "No credential values were displayed."
