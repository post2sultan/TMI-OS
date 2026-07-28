# HOTFIX-03 — Campaign-specific analysis persistence

## Cause

The semantic-duplicate shortcut returned an analysis belonging to a different
campaign. The request returned success, but no result existed for the requested
campaign, so the UI subsequently received 404.

## Fix

Every analysis request now generates and persists an assessment for the exact
requested campaign. Similarity remains available for retrieval and comparison,
but can no longer substitute another campaign's assessment.

## Validation

- Focused regression suite: 15/15 passed.
- Runtime gate analyzes campaign 167 and requires a persisted seven-dimension
  response with `campaign_id=167`.
- Local Ollama only; paid API credits: 0.
