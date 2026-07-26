# TMI OS P1-03 — Evidence Deduplication

Adds campaign-scoped duplicate detection for extracted evidence.

Each extraction now receives a canonical URL and normalized SHA-256 content
hash. Documents are compared only within their campaign, first by exact
canonical URL or hash and then by deterministic semantic similarity.
Duplicates remain auditable but are marked `duplicate`, linked to the original
document, and assigned a similarity score.
