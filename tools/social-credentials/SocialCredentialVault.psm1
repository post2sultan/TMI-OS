Set-StrictMode -Version Latest

function Protect-TmiSecret {
    param([Parameter(Mandatory)][SecureString]$Value)
    return ConvertFrom-SecureString -SecureString $Value
}

function Unprotect-TmiSecret {
    param([Parameter(Mandatory)][string]$Value)
    $secure = ConvertTo-SecureString -String $Value
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
    }
}

function Save-TmiSocialVault {
    param(
        [Parameter(Mandatory)][hashtable]$Values,
        [Parameter(Mandatory)][string]$Path
    )
    $encrypted = [ordered]@{
        version = 1
        owner = [Security.Principal.WindowsIdentity]::GetCurrent().Name
        created_at = (Get-Date).ToUniversalTime().ToString("o")
        values = [ordered]@{}
    }
    foreach ($key in $Values.Keys) {
        $encrypted.values[$key] = Protect-TmiSecret $Values[$key]
    }
    $encrypted | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $Path -Encoding utf8
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    & icacls $Path /inheritance:r /grant:r "${identity}:(M)" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Could not restrict vault permissions." }
}

function Test-TmiSocialVault {
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { throw "Credential vault was not found." }
    $vault = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
    $required = @(
        "YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN",
        "YOUTUBE_CHANNEL_ID", "META_APP_ID", "META_APP_SECRET",
        "META_ACCESS_TOKEN", "META_PAGE_ID", "INSTAGRAM_ACCOUNT_ID",
        "TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_ACCESS_TOKEN",
        "TIKTOK_OPEN_ID", "LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET",
        "LINKEDIN_ACCESS_TOKEN", "LINKEDIN_AUTHOR_URN"
    )
    foreach ($key in $required) {
        $cipher = $vault.values.$key
        if (-not $cipher) { throw "Credential $key is missing." }
        $plain = Unprotect-TmiSecret $cipher
        if ([string]::IsNullOrWhiteSpace($plain)) { throw "Credential $key is empty." }
        $plain = $null
    }
    return $true
}

Export-ModuleMember -Function Protect-TmiSecret,Unprotect-TmiSecret,Save-TmiSocialVault,Test-TmiSocialVault
