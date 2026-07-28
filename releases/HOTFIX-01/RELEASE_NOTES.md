# HOTFIX-01 — Normalize Known Dimension Extras

Local models may return `summary`, `strengths`, and `weaknesses` inside each
dimension. The parser now safely moves useful list content to the root analysis,
uses a dimension summary as fallback reasoning, and removes the known extras
before strict schema validation.

The exact failed production response from run 22 passes after this change.
Validation performs no new AI generation and consumes no paid API credits.
