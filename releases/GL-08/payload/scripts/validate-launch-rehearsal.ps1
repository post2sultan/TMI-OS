param([string]$Root = "O:\TMI-OS")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$EvidenceRoot = Join-Path $Root "rehearsal-evidence"
$BackupRoot = Join-Path $EvidenceRoot "data"

docker compose --env-file (Join-Path $Root "docker\production.env.example") `
    -f (Join-Path $Root "docker\compose.production.yml") build backend frontend
if ($LASTEXITCODE -ne 0) { throw "Production image build failed." }

& (Join-Path $Root "scripts\validate-supply-chain.ps1") -Root $Root
& (Join-Path $Root "scripts\validate-observability.ps1") -Root $Root
& (Join-Path $Root "scripts\validate-operations.ps1") -Root $Root

& (Join-Path $Root "scripts\backup-data.ps1") -Root $Root -OutputRoot $BackupRoot
$Latest = Get-ChildItem $BackupRoot -Directory |
    Where-Object Name -match '^\d{8}T\d{6}Z$' |
    Sort-Object Name -Descending | Select-Object -First 1
if ($null -eq $Latest) { throw "Rehearsal backup was not created." }
& (Join-Path $Root "scripts\validate-data-restore.ps1") -BackupPath $Latest.FullName

$RequiredRunbooks = @(
    "docs\OPERATIONS.md", "docs\INCIDENT_RESPONSE.md",
    "docs\CREDENTIAL_ROTATION.md", "docs\DATA_RECOVERY.md",
    "docs\OBSERVABILITY.md", "docs\LAUNCH_ACCEPTANCE.md"
)
foreach ($Runbook in $RequiredRunbooks) {
    if (-not (Test-Path (Join-Path $Root $Runbook))) {
        throw "Required launch runbook missing: $Runbook"
    }
}
Write-Host "GL-08 launch rehearsal PASSED."
Write-Host "Evidence backup: $($Latest.FullName)"
Write-Host "Decision remains NO-GO until explicit owner approval after merge."
