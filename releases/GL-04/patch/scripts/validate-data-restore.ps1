param(
    [Parameter(Mandatory = $true)][string]$BackupPath,
    [int]$RtoTargetMinutes = 30
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$BackupPath = [IO.Path]::GetFullPath($BackupPath)
$Manifest = Get-Content (Join-Path $BackupPath "manifest.json") -Raw | ConvertFrom-Json
$ChecksumLines = Get-Content (Join-Path $BackupPath "checksums.sha256")
foreach ($Line in $ChecksumLines) {
    $Parts = $Line -split '\s+', 2
    $Actual = (Get-FileHash (Join-Path $BackupPath $Parts[1]) -Algorithm SHA256).Hash
    if ($Actual -ne $Parts[0]) { throw "Checksum mismatch: $($Parts[1])" }
}

$Started = Get-Date
$Suffix = [Guid]::NewGuid().ToString("N").Substring(0, 8)
$Network = "tmi-gl04-$Suffix"
$Postgres = "tmi-gl04-postgres-$Suffix"
$Qdrant = "tmi-gl04-qdrant-$Suffix"
$RestoreRoot = Join-Path ([IO.Path]::GetTempPath()) "tmi-gl04-$Suffix"
$PostgresPassword = "gl04-restore-password"

New-Item -ItemType Directory -Force $RestoreRoot | Out-Null
try {
    tar -xzf (Join-Path $BackupPath $Manifest.qdrant.file) -C $RestoreRoot
    if ($LASTEXITCODE -ne 0) { throw "Qdrant archive extraction failed." }
    docker network create $Network | Out-Null

    docker run -d --name $Postgres --network $Network --tmpfs /var/lib/postgresql/data `
        -e POSTGRES_DB=restore_probe -e POSTGRES_USER=restore_probe `
        -e POSTGRES_PASSWORD=$PostgresPassword `
        postgres@sha256:de1e13ca94377fa5a27aafd0e9fc200df9692b15152f0090fdf074074ea5e397 |
        Out-Null
    for ($Attempt = 1; $Attempt -le 30; $Attempt++) {
        docker exec $Postgres pg_isready -U restore_probe -d restore_probe | Out-Null
        if ($LASTEXITCODE -eq 0) { break }
        if ($Attempt -eq 30) { throw "Restore PostgreSQL did not become ready." }
        Start-Sleep -Seconds 1
    }
    docker cp (Join-Path $BackupPath $Manifest.postgres.file) "$($Postgres):/tmp/restore.dump"
    docker exec $Postgres pg_restore -U restore_probe -d restore_probe `
        --no-owner --no-acl /tmp/restore.dump
    if ($LASTEXITCODE -ne 0) { throw "PostgreSQL restore failed." }
    $RestoredTables = [int]((docker exec $Postgres psql -U restore_probe `
        -d restore_probe -tAc `
        "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';" |
        Out-String).Trim())
    if ($RestoredTables -ne [int]$Manifest.postgres.public_table_count) {
        throw "PostgreSQL restored table count does not match."
    }

    docker run -d --name $Qdrant --network $Network `
        -v "$($RestoreRoot):/qdrant/storage" `
        qdrant/qdrant@sha256:0bd98fa7977f1e75694779359ca4e212822e5a71334e28421182f72f209d5286 |
        Out-Null
    $ExpectedCollections = @($Manifest.qdrant.collections.PSObject.Properties)
    for ($Attempt = 1; $Attempt -le 60; $Attempt++) {
        $Raw = docker run --rm --network $Network --entrypoint python `
            tmi-platform-backend -c `
            "import requests; print(requests.get('http://$($Qdrant):6333/collections',timeout=3).text)"
        if ($LASTEXITCODE -eq 0 -and ($Raw | Out-String) -match '"status":"ok"') { break }
        if ($Attempt -eq 60) { throw "Restore Qdrant did not become ready." }
        Start-Sleep -Seconds 1
    }
    foreach ($Collection in $ExpectedCollections) {
        $RawCount = docker run --rm --network $Network --entrypoint python `
            tmi-platform-backend -c `
            "import requests; print(requests.post('http://$($Qdrant):6333/collections/$($Collection.Name)/points/count',json={'exact':True},timeout=5).json()['result']['count'])"
        $RestoredCount = [int](($RawCount | Where-Object { $_ -match '^\d+$' } |
            Select-Object -Last 1 | Out-String).Trim())
        if ($RestoredCount -ne [int]$Collection.Value) {
            throw "Qdrant point count mismatch: $($Collection.Name)"
        }
    }

    $ElapsedMinutes = ((Get-Date) - $Started).TotalMinutes
    if ($ElapsedMinutes -gt $RtoTargetMinutes) {
        throw "Restore exceeded the $RtoTargetMinutes minute RTO."
    }
    Write-Host "Isolated data restore validation PASSED."
    Write-Host "Restore minutes: $([math]::Round($ElapsedMinutes, 2))"
}
finally {
    foreach ($Container in @($Qdrant, $Postgres)) {
        if (docker ps -a --format '{{.Names}}' | Where-Object { $_ -eq $Container }) {
            docker rm -f $Container | Out-Null
        }
    }
    if (docker network ls --format '{{.Name}}' | Where-Object { $_ -eq $Network }) {
        docker network rm $Network | Out-Null
    }
    if (Test-Path $RestoreRoot) {
        Remove-Item -Recurse -Force $RestoreRoot
    }
}
