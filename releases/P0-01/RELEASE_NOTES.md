# TMI OS P0-01 — Analysis Quality Validation

Enforces deterministic quality checks before an analysis can be scored or persisted.

An analysis is rejected when:

- every dimension has the same score;
- every dimension has identical reasoning;
- reasoning or evidence copies response-template placeholders;
- the summary is missing, too short, or uses the automatic fallback;
- strengths, weaknesses, or recommendations are empty; or
- the output contains no campaign-specific language.

Rejected output is logged, the database transaction is rolled back, and the API returns a structured HTTP 422 response. No database migration is required.
