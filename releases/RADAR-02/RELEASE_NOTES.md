# RADAR-02 — Safe Google News Links

## Outcome

Campaign Radar no longer exposes Google News wrapper URLs as campaign sources.

- High-confidence headline matches reuse an already discovered direct publisher
  URL.
- Unresolved wrappers are suppressed rather than guessed.
- SearXNG and Google News RSS remain free local discovery inputs.
- No paid provider or decoding service is introduced.

## Safety

The installer creates a timestamped backup, validates focused tests and a live
discovery run, and automatically rolls back on failure.

```powershell
& "O:\TMI-OS\releases\RADAR-02\install.ps1"
& "O:\TMI-OS\releases\RADAR-02\validate.ps1"
& "O:\TMI-OS\releases\RADAR-02\rollback.ps1"
```
