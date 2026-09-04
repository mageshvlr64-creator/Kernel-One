# Performance Requirements (Index)

> Canonical entry point. Every specific budget below is labeled with its provenance
> (CONFIG DEFAULT / DESIGN LIMIT / BENCHMARKED) per the same discipline as
> `runtime/11_retry_policy.md` — no unlabeled number appears in this directory.

## Budget files

| File | Covers |
|---|---|
| `02_latency_budgets.md` | Per-operation-class response time targets |
| `03_memory_budgets.md` | RAM budgets per service |
| `04_cpu_budgets.md` | CPU budgets per service |
| `05_gpu_budgets.md` | VRAM budgets per model/capability |
| `06_storage_budgets.md` | Disk/object storage growth assumptions |
| `07_concurrency_limits.md` | Max concurrent requests/tasks per resource |
| `08_agent_performance.md` | Agent planning/execution specific budgets |
| `09_rag_performance.md` | Retrieval-specific budgets |
| `10_document_processing_performance.md` | Ingestion/OCR-specific budgets |
| `11_model_routing_performance.md` | Router decision latency |
| `12_scaling_limits.md` | Where V1's single-node design stops scaling |

## Master rule (REQ-PERF-001, DEC-014)

Every number in this directory is a target to test against, not a guaranteed SLA, until
`DEC-014` (benchmark validation against pinned models, `20_DECISION_LOG.md`) is resolved.
