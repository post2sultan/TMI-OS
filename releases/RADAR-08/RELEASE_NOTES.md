# RADAR-08 — Candidate command center

- Replaces the URL-oriented Radar view with a ranked campaign-candidate command center.
- Shows trend, confidence, signal/source corroboration, matched entities, rationale, and source health.
- Supports watchlist scans and early/corroborated/promoted filters.
- Adds explicit, idempotent owner confirmation from candidate to campaign.
- Keeps all automatic discovery isolated from the campaign review and publishing workflow.
- Uses existing local services with zero paid API cost.

Rollback is available through `rollback.ps1`; production deployment automatically backs up data first.
