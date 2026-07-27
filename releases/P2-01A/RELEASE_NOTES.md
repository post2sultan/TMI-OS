# P2-01A — Prompt Contract v2

Remove copyable placeholder assessment values from the analysis prompt and
replace them with a schema-only output contract.

## Hard ceiling

- Fixed approved campaign: 109
- Models: qwen2.5 3B and 7B
- Runs: two per model, four total
- Paid API credits: 0
- Production persistence: disabled
- Production model/configuration: unchanged

Acceptance requires two quality-passing runs from at least one model.

## Result

Both models passed 2/2 runs. The 3B model averaged 221.37 seconds versus 406.40
seconds for 7B and used less than half the loaded model memory. Prompt v2 is
accepted; production should retain `qwen2.5:3b`.
