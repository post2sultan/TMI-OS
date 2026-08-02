# RADAR-06 — Free multi-source monitoring

- Adds managed RSS, Atom, and sitemap sources with independent health state.
- Polls only due enabled sources, with a ceiling of 10 sources and 50 items per source per run.
- Isolates source failures so one unavailable feed cannot stop Radar.
- Persists discoveries as signals and clusters; it never creates campaigns automatically.
- Includes a local runner and optional hourly Windows scheduled-task installer.
- Requires no paid API and adds no dependency.

Rollback: run `rollback.ps1` with the previous release tag; the deployment workflow restores from its automatic pre-deployment backup when needed.
