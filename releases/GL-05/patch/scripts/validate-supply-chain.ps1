param(
    [string]$Root = "O:\TMI-OS",
    [switch]$SkipRuntime
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$PackageJson = Get-Content (Join-Path $Root "frontend\package.json") -Raw |
    ConvertFrom-Json
foreach ($Group in @("dependencies", "devDependencies")) {
    foreach ($Dependency in $PackageJson.$Group.PSObject.Properties) {
        if ($Dependency.Value -notmatch '^\d+\.\d+\.\d+([-.][0-9A-Za-z.-]+)?$') {
            throw "Frontend dependency is not exactly pinned: $($Dependency.Name)"
        }
    }
}

$Requirements = Get-Content (Join-Path $Root "backend\requirements.txt") |
    Where-Object { $_.Trim() -and -not $_.Trim().StartsWith("#") }
foreach ($Requirement in $Requirements) {
    if ($Requirement -notmatch '^[A-Za-z0-9_.-]+(\[[A-Za-z0-9_,.-]+\])?==[A-Za-z0-9_.+-]+$') {
        throw "Python dependency is not exactly pinned: $Requirement"
    }
}

Push-Location (Join-Path $Root "frontend")
try {
    $NpmCommand = if ($env:OS -eq "Windows_NT") { "npm.cmd" } else { "npm" }
    $AuditText = & $NpmCommand audit --json 2>$null | Out-String
    $Audit = $AuditText | ConvertFrom-Json
}
finally {
    Pop-Location
}
$ExceptionFile = Join-Path $Root "security\npm-audit-exceptions.json"
$Exceptions = (Get-Content $ExceptionFile -Raw | ConvertFrom-Json).exceptions
$Allowed = @{}
foreach ($Exception in $Exceptions) {
    if ([datetime]$Exception.expires -lt (Get-Date).Date) {
        throw "Expired npm audit exception: $($Exception.advisory)"
    }
    $Allowed[$Exception.advisory] = $Exception
}

$Unhandled = @()
foreach ($Vulnerability in $Audit.vulnerabilities.PSObject.Properties.Value) {
    foreach ($Advisory in @($Vulnerability.via | Where-Object { $_ -isnot [string] })) {
        if ($Advisory.severity -in @("high", "critical")) {
            $Id = ([uri]$Advisory.url).Segments[-1].TrimEnd("/")
            if (-not $Allowed.ContainsKey($Id)) { $Unhandled += $Id }
        }
    }
}
if ($Unhandled) {
    throw "Unhandled high/critical npm advisories: $($Unhandled -join ', ')"
}

Push-Location (Join-Path $Root "frontend")
try {
    node -e "const p=require('./package-lock.json'); const bad=Object.entries(p.packages).filter(([n,v])=>n&&v.resolved&&!v.integrity); if(bad.length){console.error(bad.map(([n])=>n).join(','));process.exit(1)}"
    if ($LASTEXITCODE -ne 0) { throw "Lockfile integrity metadata is incomplete." }
}
finally {
    Pop-Location
}

if (-not $SkipRuntime) {
    $AlembicHeads = docker compose -f (Join-Path $Root "docker\compose.yml") `
        exec -T backend alembic heads
    if (@($AlembicHeads | Where-Object { $_ -match '\(head\)' }).Count -ne 1) {
        throw "Alembic must have exactly one migration head."
    }
    docker compose -f (Join-Path $Root "docker\compose.yml") `
        exec -T backend pip check
    if ($LASTEXITCODE -ne 0) { throw "Python dependency consistency check failed." }
}

Write-Host "Supply-chain policy validation PASSED."
Write-Host "Direct dependencies: exactly pinned"
Write-Host "Lockfile integrity metadata: present"
Write-Host "High/critical advisories: remediated or unexpired contextual exception"
Write-Host "Migration graph: single head"
