# Changelog

## P1-07

- Added sequential analysis versions per campaign.
- Added predecessor links and a database uniqueness constraint.
- Persisted prompt and model versions on successful analyses.
- Persisted reviewer notes separately from decision reasons.
- Backfilled all existing analysis version chains.
- Added versioning regression tests.
- Marked P1-07 complete.
- Added backup, install, validation, rollback, and reinstall automation.
