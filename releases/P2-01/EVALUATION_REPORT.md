# P2-01 Local Model Evaluation Report

## Decision

**Do not migrate the production model.**

Production remains on `qwen2.5:3b`. Neither evaluated model passed the current
analysis quality gate, and `qwen2.5:7b` did not justify its higher runtime and
memory cost.

## Fixed evaluation

- Campaign: 109, an approved real campaign with persisted publisher content
- Models: `qwen2.5:3b`, `qwen2.5:7b`
- Runs: two per model, four total
- Temperature: 0
- Persistence: disabled
- Paid API credits: 0
- Processor: CPU

## Results

| Metric | qwen2.5:3b | qwen2.5:7b |
|---|---:|---:|
| JSON-compliant runs | 2/2 | 2/2 |
| Seven-dimension runs | 2/2 | 2/2 |
| Quality-gate passes | 0/2 | 0/2 |
| Average duration | 278.49 s | 397.77 s |
| Loaded model size | 2.41 GB | 5.46 GB |
| Evidence URL accuracy | 100% | 100% |
| Score spread between runs | 0 | 0 |
| Paid API credits | 0 | 0 |

## Root cause

Every run produced a score of 50 for all seven dimensions. The 3B model also
copied placeholder reasoning and evidence from the committed response example.
The 7B model produced stronger campaign-specific reasoning but retained the
uniform example scores.

This indicates prompt/example anchoring rather than a JSON-schema or model
availability problem. A larger model alone does not resolve it.

## Next gate

Correct the prompt contract so it describes the schema without supplying
copyable placeholder scores, reasoning, evidence, or summary text. Then rerun
the same four-run ceiling before reconsidering P2-02.
