# P2-01 — Bounded Local Model Evaluation

## Evaluation ceiling

- Models: `qwen2.5:3b` and `qwen2.5:7b`
- Fixed campaign: approved campaign 109
- Runs per model: 2
- Maximum generations: 4
- Temperature: 0
- Paid API credits: 0

The evaluation measures JSON compliance, dimension completeness, quality-gate
success, evidence URL accuracy, unsupported evidence-token rate, score
consistency, duration, loaded model size, and CPU/GPU placement.

Production remains on `qwen2.5:3b`. P2-01 does not authorize migration.

## Evaluation decision

P2-01 completed with a **no migration** decision. Both models returned valid
JSON with all seven dimensions, but both copied the example score of 50 across
every dimension and failed the quality gate. The 7B model was also slower and
larger. See `EVALUATION_REPORT.md` for the recorded evidence and next gate.
