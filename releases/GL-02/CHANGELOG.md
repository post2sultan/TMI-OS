# Changelog

## GL-02

- Added digest-pinned production images and Python base image.
- Removed host port exposure from PostgreSQL, Ollama, Qdrant, Redis, and SearXNG.
- Added health-gated dependency startup and durable named volumes.
- Added Redis and Qdrant authentication configuration.
- Added a read-only, non-root, capability-free backend runtime.
- Removed production source bind mounts and restricted the backend to loopback.
- Added production secret validation and placeholder rejection.
- Fixed packaged prompt resolution exposed by immutable-image validation.
- Added automated production container build and runtime probing.
- Added backup, install, validation, rollback, and reinstall automation.
