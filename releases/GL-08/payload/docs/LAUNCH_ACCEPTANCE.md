# TMI OS Launch Acceptance

Automated rehearsal result: PASSED.

Launch remains prohibited until every automated check passes on the exact
release commit and an authorized owner records an explicit GO decision.

## Required evidence

- Production backend and frontend images build from pinned bases.
- Backend regression tests and frontend lint/build pass.
- Dependency, migration, and vulnerability policies pass.
- Production Compose, Prometheus, alert rules, and uptime probes validate.
- A clean production-like staging deployment passes API, web, metrics, and all
  five dependency readiness checks.
- PostgreSQL and Qdrant backup checksums and isolated restore pass within RTO.
- Deployment rollback images exist and the source release rollback passes.
- Incident, credential rotation, deployment, rollback, and recovery runbooks
  are present.
- Repository contains no generated credentials or placeholder production
  secrets outside example files.

## Explicit approval

After PR merge and successful CI, the launch owner must create the change
record with release commit/tag, domain, backup location, staging evidence,
monitoring destination, rollback tag, operator, launch window, and the exact
decision `GO`. A missing or ambiguous decision means NO-GO.
