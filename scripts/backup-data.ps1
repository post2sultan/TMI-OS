param(
    [string]$Root = "O:\TMI-OS",
    [string]$OutputRoot = "",
    [string]$OffsiteRoot = "",
    [int]$RetentionDays = 30,
    [string]$PostgresContainer = "tmi-postgres",
    [string]$QdrantContainer = "tmi-qdrant",
    [string]$BackendContainer = "tmi-backend"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if (-not $OutputRoot) { $OutputRoot = Join-Path $Root "data-backups" }
$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$Incomplete = Join-Path $OutputRoot ".$Timestamp.incomplete"
$Destination = Join-Path $OutputRoot $Timestamp
$QdrantStoppedAt = $null

function Get-ContainerEnvironment([string]$Container, [string]$Name) {
    $Prefix = "$Name="
    return docker inspect $Container --format '{{range .Config.Env}}{{println .}}{{end}}' |
        Where-Object { $_ -like "$Prefix*" } |
        ForEach-Object { $_.Substring($Prefix.Length) } |
        Select-Object -First 1
}

try {
    New-Item -ItemType Directory -Force $Incomplete | Out-Null
    $PostgresUser = Get-ContainerEnvironment $PostgresContainer "POSTGRES_USER"
    $PostgresDatabase = Get-ContainerEnvironment $PostgresContainer "POSTGRES_DB"
    if (-not $PostgresUser -or -not $PostgresDatabase) {
        throw "PostgreSQL container metadata is incomplete."
    }

    $TableCount = [int]((docker exec $PostgresContainer psql -U $PostgresUser `
        -d $PostgresDatabase -tAc `
        "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';" |
        Out-String).Trim())
    docker exec $PostgresContainer pg_dump -U $PostgresUser -d $PostgresDatabase `
        --format=custom --no-owner --no-acl --file=/tmp/tmi-gl04.dump
    if ($LASTEXITCODE -ne 0) { throw "PostgreSQL backup failed." }
    docker cp "$($PostgresContainer):/tmp/tmi-gl04.dump" `
        (Join-Path $Incomplete "postgres.dump")
    if ($LASTEXITCODE -ne 0) { throw "Could not copy PostgreSQL backup." }
    docker exec $PostgresContainer rm -f /tmp/tmi-gl04.dump

    $QdrantInventoryRaw = docker exec $BackendContainer python -c `
        "import json,os,requests; u='http://qdrant:6333'; h={'api-key':os.environ['QDRANT_API_KEY']}; cs=requests.get(u+'/collections',headers=h,timeout=10).json()['result']['collections']; print(json.dumps({c['name']:requests.post(u+'/collections/'+c['name']+'/points/count',headers=h,json={'exact':True},timeout=10).json()['result']['count'] for c in cs}))"
    if ($LASTEXITCODE -ne 0) { throw "Qdrant inventory failed." }
    $QdrantInventory = ($QdrantInventoryRaw | Where-Object { $_ -match '^\{' } |
        Select-Object -Last 1 | ConvertFrom-Json)

    $QdrantStoppedAt = Get-Date
    docker stop --time 30 $QdrantContainer | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Could not freeze Qdrant for backup." }
    docker run --rm --volumes-from $QdrantContainer `
        -v "$($Incomplete):/backup" --entrypoint tar `
        caddy:2-alpine -czf /backup/qdrant-storage.tar.gz -C /qdrant/storage .
    if ($LASTEXITCODE -ne 0) { throw "Qdrant storage backup failed." }
    docker start $QdrantContainer | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Could not restart Qdrant." }
    $QdrantDowntimeSeconds = [math]::Round(((Get-Date) - $QdrantStoppedAt).TotalSeconds, 2)
    $QdrantStoppedAt = $null

    $Manifest = [ordered]@{
        format_version = 1
        created_utc = (Get-Date).ToUniversalTime().ToString("o")
        rpo_target_hours = 24
        rto_target_minutes = 30
        retention_days = $RetentionDays
        postgres = [ordered]@{
            database = $PostgresDatabase
            public_table_count = $TableCount
            file = "postgres.dump"
        }
        qdrant = [ordered]@{
            collections = $QdrantInventory
            downtime_seconds = $QdrantDowntimeSeconds
            file = "qdrant-storage.tar.gz"
        }
    }
    $Manifest | ConvertTo-Json -Depth 8 |
        Set-Content (Join-Path $Incomplete "manifest.json") -Encoding UTF8
    Get-ChildItem $Incomplete -File |
        Where-Object Name -ne "checksums.sha256" |
        ForEach-Object { "$(Get-FileHash $_.FullName -Algorithm SHA256 | Select-Object -ExpandProperty Hash)  $($_.Name)" } |
        Set-Content (Join-Path $Incomplete "checksums.sha256") -Encoding ASCII

    Move-Item -LiteralPath $Incomplete -Destination $Destination

    if ($OffsiteRoot) {
        $ResolvedOutput = [IO.Path]::GetFullPath($OutputRoot).TrimEnd('\')
        $ResolvedOffsite = [IO.Path]::GetFullPath($OffsiteRoot).TrimEnd('\')
        if ($ResolvedOffsite -eq $ResolvedOutput -or $ResolvedOffsite.StartsWith("$ResolvedOutput\")) {
            throw "OffsiteRoot must be outside OutputRoot."
        }
        New-Item -ItemType Directory -Force $OffsiteRoot | Out-Null
        Copy-Item -Recurse -Force $Destination (Join-Path $OffsiteRoot $Timestamp)
    }

    $Cutoff = (Get-Date).ToUniversalTime().AddDays(-$RetentionDays)
    Get-ChildItem $OutputRoot -Directory |
        Where-Object { $_.Name -match '^\d{8}T\d{6}Z$' -and $_.LastWriteTimeUtc -lt $Cutoff } |
        Remove-Item -Recurse -Force

    Write-Host "Data backup PASSED."
    Write-Host "Backup: $Destination"
    Write-Host "Qdrant downtime seconds: $QdrantDowntimeSeconds"
}
finally {
    if ($QdrantStoppedAt) {
        docker start $QdrantContainer | Out-Null
    }
    if (Test-Path $Incomplete) {
        Remove-Item -Recurse -Force $Incomplete
    }
}
