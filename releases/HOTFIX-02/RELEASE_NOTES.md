# HOTFIX-02 — Analysis result rendering

Production-blocking fix for the blank dashboard after a completed analysis.

## Cause

Dimension evidence is returned as structured objects. The deployed component
rendered each object directly as a React child, causing a fatal render error.

## Fix

- Render structured evidence safely.
- Support the backend's `dimension` and `reasoning` field names.
- Add an application error boundary with a recovery action.
- Preserve the campaign review controls.

## Validation

- Production frontend build and lint pass.
- Production frontend health passes.
- Campaign 145's seven-dimension response shape passes.
- No AI generation or paid API usage is required.
