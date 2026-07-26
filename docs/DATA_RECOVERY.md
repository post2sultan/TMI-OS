# Data protection and recovery

## Objectives

- Recovery point objective (RPO): 24 hours.
- Recovery time objective (RTO): 30 minutes.
- Local retention: 30 days by default.
- Every completed backup contains PostgreSQL and Qdrant data, a manifest, and
  SHA-256 checksums.
- A production schedule must supply `-OffsiteRoot` on storage outside the
  application host. A local folder is not an off-machine copy.

## Backup

Run `scripts\backup-data.ps1` daily. PostgreSQL uses a consistent logical dump.
Qdrant is stopped briefly while its storage is compressed, then automatically
restarted. Incomplete backups are removed and are never published as completed
backup folders.

Example:

```powershell
.\scripts\backup-data.ps1 `
  -Root O:\TMI-OS `
  -OutputRoot E:\TMI-Backups `
  -OffsiteRoot \\backup-server\TMI-OS `
  -RetentionDays 30
```

## Restore verification

The validation script verifies every checksum, restores PostgreSQL and Qdrant
into temporary isolated containers, compares table and point counts, measures
the recovery duration, and removes the temporary environment:

```powershell
.\scripts\validate-data-restore.ps1 -BackupPath E:\TMI-Backups\<timestamp>
```

Never restore directly over active production volumes. First validate the
backup in isolation, stop application writes, preserve the current volumes,
restore into new volumes, validate health and counts, and then switch services
to the recovered volumes. Retain the preserved volumes until acceptance.
