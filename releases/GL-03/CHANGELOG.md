# GL-03 changelog

- Added a digest-pinned multi-stage frontend image.
- Added automatic HTTPS and domain configuration through Caddy.
- Added HTTP Basic authentication and strict browser security headers.
- Added a same-origin `/api` proxy with server-side credential injection.
- Removed API credentials from browser requests and production bundles.
- Removed the backend host port from the production stack.
- Added automated install, validation, backup, rollback, and runtime checks.
