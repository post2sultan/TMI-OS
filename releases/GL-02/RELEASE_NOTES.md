# TMI OS GL-02 — Production Container Isolation

Adds a separate production Compose stack with digest-pinned infrastructure,
private service networking, durable named volumes, dependency health gates,
and an immutable non-root backend. Production startup rejects default, missing,
or placeholder database, API, Qdrant, and Redis credentials.
