# P2-01A Prompt-v2 Evaluation Report

## Decision

**Adopt prompt v2 and retain `qwen2.5:3b`.**

Both models passed the quality gate in both capped runs. The 3B model was
substantially faster and smaller while producing comparable scores and higher
average confidence. A model migration is not justified.

## Results

| Metric | qwen2.5:3b | qwen2.5:7b |
|---|---:|---:|
| Valid runs | 2/2 | 2/2 |
| Scores | 83.8, 81.7 | 82.5, 82.5 |
| Average duration | 221.37 s | 406.40 s |
| Loaded size | 2.41 GB | 5.46 GB |
| Evidence URL accuracy | 100% | 100% |
| Score spread | 2.1 | 0 |
| Paid API credits | 0 | 0 |

## Comparison with prompt v1

Prompt v1 produced zero valid runs from either model because both copied the
example score of 50. Prompt v2 removed copyable assessment values and produced
four valid runs out of four.

## Production recommendation

Deploy prompt v2 with provenance `analysis-v2`. Keep `qwen2.5:3b` as the primary
model. Do not perform P2-02 model migration unless future evidence shows a
quality regression or a new workload that the 3B model cannot satisfy.
