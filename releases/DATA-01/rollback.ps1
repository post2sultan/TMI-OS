param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\DATA-01"
$LatestBackupFile = Join-Path $Release ".latest-backup.txt"
$Postgres = "tmi-production-postgres-1"

if (-not (Test-Path $LatestBackupFile)) {
    throw "No DATA-01 backup reference exists."
}
$Backup = (Get-Content -LiteralPath $LatestBackupFile -Raw).Trim()
$Manifest = Join-Path $Backup "campaign-statuses.csv"
if (-not (Test-Path $Manifest)) {
    throw "DATA-01 status manifest was not found."
}

$Environment = docker inspect $Postgres --format '{{range .Config.Env}}{{println .}}{{end}}'
$User = ($Environment | Where-Object { $_ -like "POSTGRES_USER=*" } |
    Select-Object -First 1).Substring("POSTGRES_USER=".Length)
$Database = ($Environment | Where-Object { $_ -like "POSTGRES_DB=*" } |
    Select-Object -First 1).Substring("POSTGRES_DB=".Length)

$Cases = @()
$Ids = @()
foreach ($Line in Get-Content -LiteralPath $Manifest) {
    if ($Line -notmatch '^(\d+),([a-z_]+)$') {
        throw "Invalid DATA-01 manifest row: $Line"
    }
    $Id = [int]$Matches[1]
    $Status = $Matches[2]
    $Cases += "WHEN $Id THEN '$Status'"
    $Ids += $Id
}
if ($Ids.Count -lt 1) {
    throw "DATA-01 manifest is empty."
}

$Sql = "UPDATE campaigns SET status=CASE id $($Cases -join ' ') END WHERE id IN ($($Ids -join ','));"
docker exec $Postgres psql -U $User -d $Database -v ON_ERROR_STOP=1 -c $Sql
if ($LASTEXITCODE -ne 0) {
    throw "DATA-01 status restoration failed."
}

Write-Host "DATA-01 rollback PASSED."
Write-Host "Restored campaign statuses: $($Ids.Count)"
