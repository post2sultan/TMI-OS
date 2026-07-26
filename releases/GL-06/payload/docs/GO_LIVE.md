# TMI OS Go-Live Path

The go-live path is executed one locked milestone at a time. A milestone must
pass install, validation, rollback, reinstall, runtime validation, and pull
request merge before the next milestone begins.

## GL-01 — API Security

Scope: authentication, role authorization, actor attribution, security audit
events, and request rate limits.

Status: Complete

## GL-02 — Production Container Isolation

Scope: internal networks, pinned images, immutable application containers,
service hardening, and production environment enforcement.

Status: Complete

## GL-03 — Production Web Entry Point

Scope: frontend container, reverse proxy, domain configuration, HTTPS, and
security headers.

Status: Complete

## GL-04 — Data Protection and Recovery

Scope: PostgreSQL and Qdrant backup, retention, off-machine copies, restore
automation, and tested RPO/RTO.

Status: Complete

## GL-05 — CI and Supply-Chain Gates

Scope: pull-request tests, frontend build and lint, migration checks,
dependency pinning, vulnerability scanning, and artifact verification.

Status: Complete

## GL-06 — Observability and Dependency Readiness

Scope: structured logs, metrics, error tracking, dependency-aware readiness,
alerts, and uptime monitoring.

Status: Complete

## GL-07 — Operations and Staging

Scope: deployment, rollback, incident, credential rotation, and recovery
runbooks plus staging end-to-end testing.

Status: Authorized, pending GL-06

## GL-08 — Launch Rehearsal

Scope: final production rehearsal, recovery proof, security checks, acceptance
criteria, and explicit go-live approval.

Status: Authorized, pending GL-07
