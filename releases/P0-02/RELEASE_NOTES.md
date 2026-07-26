# TMI OS P0-02 — Analysis Retry

Adds one deterministic correction attempt when an analysis response fails parsing, schema validation, completeness checks, or P0-01 quality validation.

- The first request uses the original strict prompt unchanged.
- The second request appends concise correction instructions and a bounded validation summary.
- Invalid JSON is returned to the pipeline for correction instead of being retried with the unchanged prompt.
- Invalid responses are never cached.
- Scoring and persistence occur only after a response passes all validation.
- A failed second response is returned as the existing clear validation error.

No database migration is required.
