# TMI OS Observability and Readiness

## Signals

- `GET /health` proves the API process is alive.
- `GET /ready` proves PostgreSQL, Qdrant, Redis, SearXNG, and Ollama are
  reachable. It returns HTTP 503 and per-dependency booleans if any required
  dependency is unavailable.
- `GET /metrics` exposes bounded Prometheus metrics without credentials or
  sensitive values.
- Every HTTP response includes `X-Request-ID`. A caller-supplied value is
  preserved up to 64 characters; otherwise TMI creates one.
- Application logs are single-line JSON. Request completion and unhandled
  exception events contain the request ID for correlation.
- Prometheus checks the API and web entry point every 15 seconds and retains
  metrics for 30 days.

Prometheus is attached only to the private production network and has no host
port. Alert rules are evaluated locally. GL-07 must connect the production
Prometheus instance to the approved notification channel and verify external
internet uptime monitoring against the final public domain.

## Alerts

Critical alerts fire after two minutes when the API, web entry point, or a
required dependency is unavailable. A warning fires when the five-minute API
server-error ratio remains above five percent for five minutes.

## Response

1. Record the alert name, start time, release tag, and request ID.
2. Check `/ready` to identify the failed dependency.
3. Correlate JSON logs using `request_id`.
4. If the failure began after deployment, use the locked release rollback.
5. If data integrity may be affected, stop writes and follow
   `docs/DATA_RECOVERY.md`.
6. Record recovery time and evidence before closing the incident.

Never paste API keys, passwords, request bodies, or full query strings into
alerts or incident notes.
