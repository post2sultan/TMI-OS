# Changelog

## P0-03

- Added the `analysis_runs` table and ORM model.
- Added independent analysis-attempt persistence.
- Added explicit `analysis-v1` prompt provenance.
- Recorded successful, validation-failed, and provider-error attempts.
- Integrated attempt telemetry with both original and corrected generations.
- Added repository and retry audit tests.
- Added a live database round-trip validator with row-count cleanup.
- Updated the backlog to mark P0-03 complete and P0-04 next.
- Added automatic backup, migration install, validation, rollback, and reinstall scripts.
