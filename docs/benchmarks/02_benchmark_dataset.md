# Benchmark Dataset

> What data each benchmark dimension is evaluated against.

## Composition

| Dataset | Used by | Source |
|---|---|---|
| Synthetic inspection-report corpus (same as `demo/03_demo_data.md`) | `04_document_benchmark.md`, `09_citation_benchmark.md` | Purpose-built, not real customer data (matches the demo's own no-proprietary-data constraint) |
| A small coding-task set (e.g. "write and test function X") | `05_coding_benchmark.md` | Purpose-built |
| A small spreadsheet-analysis set | `06_spreadsheet_benchmark.md` | Purpose-built |
| A small labeled image set (equipment photos, drawings) | `07_visual_benchmark.md` | Purpose-built; would need expansion before P&ID-specific work (`later/02_pid_analysis.md`) |
| A set of known tool-calling scenarios with expected tool sequences | `08_tool_use_benchmark.md` | Purpose-built |

## Rule

No benchmark dataset contains real, proprietary, or customer data — consistent with
`demo/03_demo_data.md`'s constraint, applied here for the same reason (avoiding any
sensitivity/licensing question in evaluation artifacts that might be shared or reviewed
externally).

## V2 expansion

`later/11_advanced_model_benchmarking.md` would expand this into a larger, versioned dataset
with a formal train/eval split discipline — V1's dataset is intentionally small and manually
curated, sufficient for informal comparison, not statistically rigorous evaluation.
