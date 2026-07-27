# DATA-01 — Archive Legacy Google Wrapper Campaigns

## Outcome

Archive unusable legacy `news.google.com` campaign records without deleting
them. Records with an analysis are excluded defensively.

## Safety

- Creates a full production PostgreSQL and Qdrant backup.
- Captures every affected campaign ID and original status.
- Preserves approved pilot campaign 109.
- Provides exact status restoration rollback.
- Uses no paid discovery or model provider.

```powershell
& "O:\TMI-OS\releases\DATA-01\install.ps1"
& "O:\TMI-OS\releases\DATA-01\validate.ps1"
& "O:\TMI-OS\releases\DATA-01\rollback.ps1"
```
