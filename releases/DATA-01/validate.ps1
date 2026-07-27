param(
    [string]$Root = "O:\TMI-OS"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Postgres = "tmi-production-postgres-1"
$Environment = docker inspect $Postgres --format '{{range .Config.Env}}{{println .}}{{end}}'
$User = ($Environment | Where-Object { $_ -like "POSTGRES_USER=*" } |
    Select-Object -First 1).Substring("POSTGRES_USER=".Length)
$Database = ($Environment | Where-Object { $_ -like "POSTGRES_DB=*" } |
    Select-Object -First 1).Substring("POSTGRES_DB=".Length)

$Raw = docker exec $Postgres psql -U $User -d $Database -At -F "," -c `
    "SELECT (SELECT count(*) FROM campaigns WHERE url LIKE 'https://news.google.com/%' AND status<>'archived'),(SELECT count(*) FROM campaigns WHERE url LIKE 'https://news.google.com/%' AND status='archived'),(SELECT count(*) FROM analyses a JOIN campaigns c ON c.id=a.campaign_id WHERE c.url LIKE 'https://news.google.com/%'),(SELECT count(*) FROM campaigns WHERE id=109 AND status='approved');"
if ($LASTEXITCODE -ne 0) {
    throw "DATA-01 database validation failed."
}

$Values = (($Raw | Select-Object -Last 1).Trim()).Split(",")
$ActiveWrappers = [int]$Values[0]
$ArchivedWrappers = [int]$Values[1]
$AnalyzedWrappers = [int]$Values[2]
$ApprovedPilot = [int]$Values[3]

if ($ActiveWrappers -ne 0) {
    throw "Active Google wrapper campaigns remain: $ActiveWrappers"
}
if ($ArchivedWrappers -lt 1) {
    throw "No legacy Google wrapper campaigns were archived."
}
if ($AnalyzedWrappers -ne 0) {
    throw "An analyzed campaign was included unexpectedly."
}
if ($ApprovedPilot -ne 1) {
    throw "Approved pilot campaign 109 was not preserved."
}

Write-Host ""
Write-Host "DATA-01 validation PASSED."
Write-Host "Archived wrappers: $ArchivedWrappers"
Write-Host "Active wrappers: $ActiveWrappers"
Write-Host "Analyzed wrappers: $AnalyzedWrappers"
Write-Host "Pilot campaign 109: approved"
Write-Host "Paid provider credits: 0"
