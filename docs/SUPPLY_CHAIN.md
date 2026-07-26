# CI and supply-chain policy

Every pull request and push to `main` runs `.github/workflows/supply-chain.yml`.
The workflow uses a commit-pinned checkout action and grants read-only contents
permission.

Required gates:

- deterministic frontend install from `package-lock.json`;
- frontend lint and production build;
- exact direct dependency pins and npm lockfile integrity metadata;
- high/critical npm advisory evaluation;
- production backend and frontend image builds;
- Python dependency consistency;
- exactly one Alembic migration head;
- all backend regression tests against the production image; and
- production browser bundle credential scanning.

Vulnerability exceptions live in `security/npm-audit-exceptions.json`. Each
exception must identify one advisory, document why the affected feature is not
used, and include an expiry date. Expired or unknown high/critical advisories
fail the gate.

The current React Router exception applies only to RSC/server-action handling.
TMI OS is a static Vite SPA and does not enable those server features. The
exception expires on 2026-08-26 and must be removed as soon as a non-vulnerable
compatible release is available.
