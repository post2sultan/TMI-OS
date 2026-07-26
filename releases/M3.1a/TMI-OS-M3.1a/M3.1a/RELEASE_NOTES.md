# TMI OS M3.1a — DiscoveryRun Persistence

## Delivered

- Persists one `discovery_runs` record for every discovery provider execution.
- Applies to both `POST /discover` and `POST /discover/save`.
- Records provider, status, result count, duration, credits and query.
- Uses a dedicated repository with transaction rollback on persistence failure.
- Keeps existing API response contracts unchanged.

## Files

- Modified: `backend/app/main.py`
- Added: `backend/app/repositories/discovery_run_repository.py`

## Install

```powershell
cd O:\TMI-OS\releases\M3.1a
powershell -ExecutionPolicy Bypass -File .\install.ps1
powershell -ExecutionPolicy Bypass -File .\validate.ps1
```

## Rollback

```powershell
powershell -ExecutionPolicy Bypass -File .\rollback.ps1
```
