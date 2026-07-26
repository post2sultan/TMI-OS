param(
    [Parameter(Mandatory = $true)][string]$SourceEnvFile,
    [Parameter(Mandatory = $true)][string]$OutputEnvFile
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$Source = [IO.Path]::GetFullPath($SourceEnvFile)
$Output = [IO.Path]::GetFullPath($OutputEnvFile)
if ($Source -eq $Output) { throw "OutputEnvFile must differ from SourceEnvFile." }
$Content = Get-Content $Source -Raw

function New-Secret([int]$Bytes = 32) {
    $Buffer = New-Object byte[] $Bytes
    $Generator = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $Generator.GetBytes($Buffer) }
    finally { $Generator.Dispose() }
    return ([BitConverter]::ToString($Buffer)).Replace("-", "").ToLowerInvariant()
}

foreach ($Name in @(
    "POSTGRES_PASSWORD", "AUTH_VIEWER_API_KEY", "AUTH_OPERATOR_API_KEY",
    "AUTH_REVIEWER_API_KEY", "AUTH_ADMIN_API_KEY", "QDRANT_API_KEY",
    "REDIS_PASSWORD", "SEARXNG_SECRET"
)) {
    $Value = New-Secret
    $Content = [regex]::Replace(
        $Content, "(?m)^$([regex]::Escape($Name))=.*$", "$Name=$Value"
    )
}
$WebPassword = New-Secret 16
$Hash = docker run --rm caddy:2-alpine caddy hash-password --plaintext $WebPassword
if ($LASTEXITCODE -ne 0) { throw "Web password hashing failed." }
$Content = [regex]::Replace(
    $Content, "(?m)^TMI_WEB_PASSWORD_HASH=.*$",
    "TMI_WEB_PASSWORD_HASH='$Hash'"
)
New-Item -ItemType Directory -Force (Split-Path -Parent $Output) | Out-Null
[IO.File]::WriteAllText($Output, $Content, [Text.UTF8Encoding]::new($false))
Write-Host "Credential bundle created: $Output"
Write-Host "One-time TMI web password: $WebPassword"
