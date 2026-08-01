# P3-MVP-05A — Platform-specific social credential vault

- Adds Instagram Login fields: app ID, app secret, and access token.
- Configures one platform at a time and preserves previously encrypted entries.
- Creates a timestamped encrypted backup before updating an existing vault.
- Keeps Windows DPAPI protection and owner-only file permissions.
- Uses no paid API or AI credits.

Run Instagram setup:

```powershell
.\tools\social-credentials\configure.ps1 -Platform Instagram
```

Validate afterwards:

```powershell
.\tools\social-credentials\verify.ps1 -Platform Instagram
```
