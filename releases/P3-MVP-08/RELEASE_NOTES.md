# P3-MVP-08 — Local LinkedIn OAuth

- Adds local LinkedIn OAuth with PKCE, CSRF state validation, and a loopback-only callback.
- Opens authorization in Brave and requests only `openid`, `profile`, and `w_member_social`.
- Encrypts the access token, expiry, scopes, and member author URN in the Windows DPAPI vault.
- Preserves existing platform entries and creates an encrypted backup before token storage.
- Includes install, validation, and rollback scripts.
- Uses no paid API or AI credits.

After merging, run:

```powershell
.\tools\social-credentials\configure.ps1 -Platform LinkedIn
.\tools\social-credentials\linkedin-authorize.ps1
.\tools\social-credentials\verify.ps1 -Platform LinkedIn
```
