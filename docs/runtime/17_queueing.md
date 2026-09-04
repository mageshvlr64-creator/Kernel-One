# Queueing

> What happens when a concurrency limit (`16_concurrency.md`,
> `performance/07_concurrency_limits.md`) is reached — queue, don't reject, up to a bounded
> queue depth.

## Queue behavior by resource

| Resource | Queue depth (CONFIG DEFAULT) | Behavior beyond queue depth |
|---|---|---|
| Model inference (per model) | 10 | `MODEL_RESOURCE_EXHAUSTED` |
| Code execution sandboxes | 5 | `SANDBOX_LIMIT_EXCEEDED`-adjacent queue-full response (distinguished from the per-execution resource limit of the same error code by context) |
| Document ingestion pipeline | 10 | New uploads accepted but held in `UPLOADED` state slightly longer before `VALIDATING` begins — not rejected, since ingestion is not latency-critical the way interactive requests are |

## V1 implementation note

Queueing in V1 is in-process (no separate message broker, per DEC-001's single-node
simplicity) — a full distributed queue (`failures/38_queue_failures.md`'s broader failure
mode) is more relevant to the V2 multi-node design (`later/08_multi_node_scaling.md`) than to
V1's current implementation.
