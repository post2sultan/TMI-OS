# P3-MVP-12 — TikTok draft upload

- Uploads the generated vertical MP4 to the authorized owner's TikTok Inbox using `video.upload`.
- Never calls the Direct Post endpoint and never makes TikTok content public automatically.
- Records queue, attempt, failure, and TikTok publish ID state in the dashboard.
- The owner reviews and completes the post from TikTok Inbox.

Rollback uses `rollback.ps1` with the previous release tag.
