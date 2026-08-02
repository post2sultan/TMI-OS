# P3-MVP-13 — LinkedIn member-feed video publishing

- Uploads the generated 1080×1080 LinkedIn video through the versioned Videos API.
- Publishes the approved caption, hashtags, and video to the authorized owner's public member feed.
- Requires explicit owner confirmation before queueing.
- Persists video URN, post URN, attempts, status, and failures.

Rollback uses `rollback.ps1` with the previous release tag.
