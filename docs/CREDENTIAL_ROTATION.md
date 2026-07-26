# Credential Rotation

Generate the next environment file with `scripts/new-credential-bundle.ps1`.
The command never overwrites its source and prints the new web password once.
Store the new file and password in the approved secret manager; never commit
them, paste them into tickets, or retain them in shell history.

## Planned rotation

1. Create the next bundle and record its secret-manager version.
2. In staging, update service-side PostgreSQL, Redis, and Qdrant credentials,
   then deploy consumers with the matching bundle.
3. Verify all five readiness checks and authenticated read/write paths.
4. Repeat in production during an approved change window, one dependency at a
   time. Keep the current credential active only where overlap is supported.
5. Revoke prior API keys and service credentials after validation.
6. Confirm old credentials fail, record evidence, and securely destroy temporary
   files.

## Emergency rotation

Treat exposure as SEV-1. Revoke the compromised credential first when safe,
generate a clean bundle on a trusted workstation, deploy affected services,
validate readiness and audit logs, and investigate use of the old credential.

Database and Qdrant credential changes must be applied server-side before their
consumer containers restart. Redis password changes require a coordinated Redis
restart. If any step fails, restore the prior secret-manager version and use the
immutable release rollback procedure.
