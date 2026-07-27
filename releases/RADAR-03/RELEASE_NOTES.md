# RADAR-03 — Provider Status UX

## Outcome

Campaign Radar now presents provider telemetry accurately:

- Backend `SUCCESS` values display as **Operational**.
- Backend `FAILED` values display as **Failed**.
- Unknown states use a neutral warning treatment.
- Each run shows its result count and whether it was free or consumed credits.

## Safety

Installation backs up the Campaign Radar page, builds and lints the frontend,
deploys only the frontend container, and rolls back automatically on failure.

```powershell
& "O:\TMI-OS\releases\RADAR-03\install.ps1"
& "O:\TMI-OS\releases\RADAR-03\validate.ps1"
& "O:\TMI-OS\releases\RADAR-03\rollback.ps1"
```
