# P3-MVP-13 — LinkedIn Page video publishing

- Uploads the generated 1080×1080 LinkedIn video through the versioned Videos API.
- Publishes only to an authorized organization Page and rejects personal-profile author URNs.
- Requires explicit owner confirmation before queueing.
- Persists video URN, post URN, attempts, status, and failures.

Rollback uses `rollback.ps1` with the previous release tag.
