param([string]$EnvFile = "O:\TMI-OS\docker\.env.production.local")
$ErrorActionPreference = "Stop"

function Read-Secret([string]$Label) {
    $secure = Read-Host $Label -AsSecureString
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
}

function Set-EnvValue([string]$Content, [string]$Name, [string]$Value) {
    if ([string]::IsNullOrWhiteSpace($Value)) { return $Content }
    if ($Value.Contains("`r") -or $Value.Contains("`n")) { throw "$Name is invalid." }
    $line = "$Name=$Value"
    if ($Content -match "(?m)^$([regex]::Escape($Name))=") {
        return [regex]::Replace($Content, "(?m)^$([regex]::Escape($Name))=.*$", $line)
    }
    return $Content.TrimEnd() + "`r`n" + $line + "`r`n"
}

$pexels = Read-Secret "Paste Pexels API key"
$pixabay = Read-Secret "Paste Pixabay API key"
if ([string]::IsNullOrWhiteSpace($pexels) -and [string]::IsNullOrWhiteSpace($pixabay)) {
    throw "At least one stock provider key is required."
}
$content = if (Test-Path -LiteralPath $EnvFile) { Get-Content -LiteralPath $EnvFile -Raw } else { "" }
$content = Set-EnvValue $content "PEXELS_API_KEY" $pexels
$content = Set-EnvValue $content "PIXABAY_API_KEY" $pixabay
$temporary = "$EnvFile.stock.tmp"
[IO.File]::WriteAllText($temporary, $content, [Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporary -Destination $EnvFile -Force
Write-Host "Stock media credentials saved privately. Values were not displayed."
