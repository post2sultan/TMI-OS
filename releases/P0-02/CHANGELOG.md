# Changelog

## P0-02

- Added a two-attempt validated generation boundary to the analysis pipeline.
- Added concise validation-aware correction prompts for the second attempt.
- Added raw-response mode to the AI router for pipeline-owned JSON validation.
- Prevented invalid JSON responses from entering the AI cache.
- Reused the same retry behavior in transient and persistent analysis paths.
- Added tests for invalid JSON, quality failures, prompt correction, retry limits, cache safety, and persistence safety.
- Updated the production backlog to mark P0-02 complete and P0-03 next.
- Added automatic backup, install, validation, runtime validation, and rollback scripts.
