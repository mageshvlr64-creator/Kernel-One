# Benchmark Overview

> Index for the model-evaluation harness referenced by `later/11_advanced_model_benchmarking.md`
> (the V2 automated version) and used informally in V1 to inform DEC-013's model pinning
> decision.

## Purpose

Provide a repeatable, comparable way to evaluate candidate models for each capability slot
(`schemas/06_model_schema.md`) before pinning one (DEC-013) — replacing "seems good in
conversation" with a specific, referenceable score per dimension.

## Dimensions

| File | Dimension |
|---|---|
| `03_reasoning_benchmark.md` | General reasoning/instruction-following |
| `04_document_benchmark.md` | Document Q&A / RAG-grounded answering |
| `05_coding_benchmark.md` | Code generation and self-correction |
| `06_spreadsheet_benchmark.md` | Spreadsheet/numeric reasoning |
| `07_visual_benchmark.md` | Vision-language description accuracy |
| `08_tool_use_benchmark.md` | Tool-calling reliability |
| `09_citation_benchmark.md` | Evidence/citation accuracy (REQ-FUNC-005-adjacent) |
| `10_hallucination_benchmark.md` | Rate of unsupported claims |
| `11_latency_benchmark.md` | Response time under `performance/02_latency_budgets.md`'s targets |
| `12_resource_benchmark.md` | VRAM/CPU footprint verification against `07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md` claims |
| `13_reliability_benchmark.md` | Failure rate / crash rate under sustained use |
| `14_router_scoring.md` | How the above dimensions combine into the Model Router's scoring function |

## V1 status

These benchmarks are **specification-only in V1** — the harness itself
(`later/11_advanced_model_benchmarking.md`) is a V2 build item. V1's model choice (DEC-013)
is made using informal/manual evaluation against this same dimension list, explicitly labeled
as such rather than presented as benchmark-verified.
