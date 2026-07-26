# TMI OS Operations Runbook

## Deployment

Every release uses an immutable `TMI_RELEASE_TAG`. Never deploy from `latest`.
Run the supply-chain gates, create an off-machine data backup for an existing
environment, and deploy with `scripts/deploy-release.ps1`. Production requires
the explicit `-ApproveProduction` switch. The command validates secrets,
renders Compose, creates the mandatory backup, builds the release images, waits
for container health, and fails without silently changing the previous tag.

Record the operator, commit, release tag, backup location, start/end time, and
validation result in the change record. Keep the previous backend and frontend
images until the observation window closes.

## Deployment rollback

Use `scripts/rollback-release.ps1` with the last known-good immutable tag. The
script refuses a malformed tag, verifies both rollback images exist, requires
explicit production approval, and waits for health. A code rollback does not
reverse database migrations or restore data.

If integrity is in doubt, stop writes and follow `docs/DATA_RECOVERY.md`.
Never run a destructive database downgrade during an incident without a tested
restore point and incident commander approval.

## Staging

`docker/compose.staging.yml` overlays production with loopback-only ports and
isolated project volumes. `scripts/validate-staging.ps1` generates temporary
credentials, deploys the full production topology, verifies API liveness and
five-dependency readiness, checks the web entry point, metrics and Prometheus
rules, then removes the isolated containers and volumes.

Production approval is prohibited unless staging passes on the exact commit and
release tag selected for production.

## Recovery and observability

- Data backup and restore: `docs/DATA_RECOVERY.md`
- Signals, alerts, and first response: `docs/OBSERVABILITY.md`
- Incident command: `docs/INCIDENT_RESPONSE.md`
- Credential rotation: `docs/CREDENTIAL_ROTATION.md`
