# Document Benchmark

> Evaluates RAG-grounded document Q&A quality — the capability most directly tied to
> REQ-FUNC-001/004/005.

## Method

Fixed questions against the synthetic inspection-report corpus (`02_benchmark_dataset.md`)
with known-correct answers and known-correct citations; scored on: answer correctness,
citation correctness (does the cited page/chunk actually support the claim), and
citation completeness (is every factual claim cited).

## Relationship to `TEST-EVIDENCE-001`

This benchmark is the broader, comparative-across-models version of the same check
`TEST-EVIDENCE-001` (`testing/09_rag_testing.md`) performs against the pinned production
model — this file is for choosing which model to pin (DEC-013); `TEST-EVIDENCE-001` is for
verifying the pinned model continues to meet the bar in CI.
