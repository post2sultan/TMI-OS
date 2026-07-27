# RADAR-01 — Reproducible SearXNG JSON Search

## Purpose

Make the working local SearXNG Campaign Radar provider reproducible after a
container rebuild without committing its runtime secret.

## Scope

- Enables HTML and JSON search formats.
- Preserves an existing runtime secret or generates a cryptographically random
  secret on first installation.
- Validates both the direct SearXNG endpoint and the backend provider.
- Creates an automatic timestamped backup before installation.
- Provides a one-command rollback.

## Commands

```powershell
& "O:\TMI-OS\releases\RADAR-01\install.ps1"
& "O:\TMI-OS\releases\RADAR-01\validate.ps1"
& "O:\TMI-OS\releases\RADAR-01\rollback.ps1"
```
