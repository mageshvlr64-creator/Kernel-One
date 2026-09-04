# Concurrency Limits

> Max concurrent requests/tasks per constrained resource, restated from
> `07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`'s per-profile concurrency expectations as
> enforced limits.

| Resource | PROFILE-B limit | Enforcement |
|---|---|---|
| Concurrent model-inference requests (per model) | 1-3 (GPU-bound) | Inference Gateway queues beyond this, does not reject outright, up to a queue depth of 10 (CONFIG DEFAULT) before returning `MODEL_RESOURCE_EXHAUSTED` |
| Concurrent Code Execution sandboxes | 3 (CPU/memory-bound, `03_cpu_budgets.md`/`03_memory_budgets.md`) | Tool Gateway queues beyond this |
| Concurrent Document Ingestion pipelines | 2 (OCR is the bottleneck) | Queued, not rejected, up to a reasonable queue depth |
| Concurrent API requests overall | Bounded by `RATE_LIMIT_PER_MINUTE` per user (`16_ENVIRONMENT_AND_CONFIGURATION.md`), not a global concurrency cap in V1 | — |

## Rule

Queuing (not rejection) is the default behavior when a concurrency limit is reached, unless the
queue itself is full — a full queue returns the appropriate `_RESOURCE_EXHAUSTED`/`_UNAVAILABLE`
error rather than blocking indefinitely.
