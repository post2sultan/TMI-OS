# P3-MVP-07 — Local TikTok OAuth

- Adds a one-click Desktop OAuth flow using a loopback callback and PKCE.
- Requests only `user.info.basic` and `video.upload` for owner-approved draft uploads.
- Exchanges the authorization code locally and encrypts access token, refresh token, creator ID, scopes, and expirations in the Windows DPAPI vault.
- Preserves existing Instagram and YouTube entries and creates an encrypted backup before token storage.
- Includes install, validation, and rollback scripts.
- Uses no paid API or AI credits.

After merging, run:

```powershell
.\tools\social-credentials\configure.ps1 -Platform TikTok
.\tools\social-credentials\tiktok-authorize.ps1
.\tools\social-credentials\verify.ps1 -Platform TikTok
```
