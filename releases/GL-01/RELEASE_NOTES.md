# TMI OS GL-01 — API Security

Adds API-key authentication, role authorization, actor attribution, per-identity
rate limits, and persistent audit events for state-changing requests. Production
configuration rejects missing or development API keys. The frontend supplies
the configured key and actor identity to the API.
