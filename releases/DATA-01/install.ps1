param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Release = Join-Path $Root "releases\DATA-01"
$Backup = Join-Path $Release "backups\$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$Manifest = Join-Path $Backup "campaign-statuses.csv"
$LatestBackupFile = Join-Path $Release ".latest-backup.txt"
$Postgres = "tmi-production-postgres-1"

function Get-ContainerValue([string]$Name) {
    $Prefix = "$Name="
    return docker inspect $Postgres --format '{{range .Config.Env}}{{println .}}{{end}}' |
        Where-Object { $_ -like "$Prefix*" } |
        ForEach-Object { $_.Substring($Prefix.Length) } |
        Select-Object -First 1
}

$User = Get-ContainerValue "POSTGRES_USER"
$Database = Get-ContainerValue "POSTGRES_DB"
if (-not $User -or -not $Database) {
    throw "Production PostgreSQL metadata is incomplete."
}

& (Join-Path $Root "scripts\backup-data.ps1") `
    -Root $Root `
    -OutputRoot (Join-Path $Root "deployment-backups\production") `
    -PostgresContainer $Postgres `
    -QdrantContainer "tmi-production-qdrant-1" `
    -BackendContainer "tmi-production-backend-1"

New-Item -ItemType Directory -Force -Path $Backup | Out-Null
$Rows = docker exec $Postgres psql -U $User -d $Database -At -F "," -c `
    "SELECT c.id,c.status FROM campaigns c WHERE c.url LIKE 'https://news.google.com/%' AND NOT EXISTS (SELECT 1 FROM analyses a WHERE a.campaign_id=c.id) ORDER BY c.id;"
if ($LASTEXITCODE -ne 0) {
    throw "Could not capture legacy campaign statuses."
}

$Rows | Set-Content -LiteralPath $Manifest -Encoding ascii
Set-Content -LiteralPath $LatestBackupFile -Value $Backup -Encoding utf8

$Updated = docker exec $Postgres psql -U $User -d $Database -At -c `
    "WITH changed AS (UPDATE campaigns c SET status='archived' WHERE c.url LIKE 'https://news.google.com/%' AND NOT EXISTS (SELECT 1 FROM analyses a WHERE a.campaign_id=c.id) AND c.status<>'archived' RETURNING 1) SELECT count(*) FROM changed;"
if ($LASTEXITCODE -ne 0) {
    throw "Legacy wrapper archival failed."
}

& (Join-Path $Release "validate.ps1") -Root $Root

Write-Host ""
Write-Host "DATA-01 installation PASSED."
Write-Host "Archived records: $((($Updated | Select-Object -Last 1).Trim()))"
Write-Host "Status manifest: $Manifest"
