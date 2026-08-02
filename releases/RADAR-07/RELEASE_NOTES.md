# RADAR-07 — Local campaign intelligence

- Matches known brands, competitors, and categories from active watchlists.
- Groups near-duplicate headlines with deterministic token similarity.
- Limits similarity checks to the 250 most recent candidates for predictable local cost.
- Adds explainable confidence and 0–100 trend scores using source corroboration, repeat detection, entity matches, and recency.
- Adds status, confidence, and trend ranking filters to the candidate API.
- Uses no paid API, hosted model, or external AI service.

Rollback is available through `rollback.ps1`; deployment creates a backup before migration.
