param([string]$Root = "O:\TMI-OS")
$ErrorActionPreference = "Stop"
& (Join-Path $Root "releases\P3-MVP-08\validate.ps1") -Root $Root
$authorize = Get-Content -LiteralPath (Join-Path $Root "tools\social-credentials\linkedin-authorize.ps1") -Raw
if ($authorize -match "native-pkce") { throw "OpenID flow must not use LinkedIn native PKCE." }
if ($authorize -match "code_challenge") { throw "OpenID flow must not send PKCE parameters." }
if ($authorize -notmatch 'openid profile w_member_social') { throw "Required least-privilege LinkedIn scopes are missing." }
Write-Host "P3-MVP-08B validation PASSED. OpenID-compatible confidential OAuth flow confirmed."
