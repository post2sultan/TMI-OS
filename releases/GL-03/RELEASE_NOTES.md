# TMI OS GL-03 — Production Web Entry Point

Adds a production frontend container and Caddy edge gateway with automatic
domain TLS, authenticated access, strict browser security headers, and a
same-origin API proxy that keeps privileged API credentials out of JavaScript.

The backend and all infrastructure services remain private. The automated
runtime probe verifies anonymous rejection, authenticated UI and API access,
immutable container settings, security headers, and absence of development
credentials in the production bundle.
