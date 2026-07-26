# Incident Response

## Roles and severity

The incident commander owns decisions and timeline. The operations lead performs
changes. The communications lead provides stakeholder updates. One person may
hold multiple roles for a small incident, but every action must name its owner.

- SEV-1: security breach, data loss, or complete outage.
- SEV-2: major feature unavailable or sustained dependency failure.
- SEV-3: degraded service with a safe workaround.

## Response

1. Open an incident record with UTC start time, severity, release tag, symptoms,
   alerts, request IDs, and named incident commander.
2. Contain risk. For suspected integrity or credential compromise, stop writes
   and revoke exposed access.
3. Diagnose with `/ready`, Prometheus alerts, and correlated JSON logs. Do not
   paste credentials, request bodies, or personal data into the record.
4. Choose one action: dependency recovery, immutable release rollback, credential
   rotation, or tested data restore.
5. Validate `/health`, `/ready`, web `/healthz`, metrics, and the affected user
   journey before declaring recovery.
6. Record recovery time, evidence, customer impact, and all commands/actions.
7. Complete a blameless review with root cause, detection gap, and owned actions.

SEV-1 and SEV-2 recovery requires explicit incident-commander approval. Preserve
logs and backups; do not delete evidence during response.
