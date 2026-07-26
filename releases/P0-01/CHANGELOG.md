# Changelog

## P0-01

- Activated the existing analysis quality validator in both pipeline entry points.
- Added deterministic campaign-specific language validation.
- Enforced validation before scoring and repository persistence.
- Added structured `analysis_quality_validation_failed` HTTP 422 responses.
- Logged rejected raw model output for production inspection.
- Added unit, persistence-boundary, and API-contract tests.
- Updated the production backlog to mark P0-01 complete and P0-02 next.
- Added automatic backup, install, validation, runtime validation, and rollback scripts.
