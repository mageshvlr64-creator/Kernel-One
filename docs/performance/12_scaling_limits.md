# Scaling Limits (V1 Single-Node)

> Where V1's architecture (`architecture/15_single_node_architecture.md`) stops scaling —
> stated explicitly so a deployment approaching these limits knows to plan for
> `later/08_multi_node_scaling.md` rather than discovering degradation unexpectedly.

| Dimension | V1 single-node ceiling (approximate, PROFILE-C) | What happens beyond it |
|---|---|---|
| Concurrent users | ~20 (per `07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md` PROFILE-C expected concurrency) | Inference queue depth grows, `07_concurrency_limits.md` queue limits start rejecting requests with `MODEL_RESOURCE_EXHAUSTED` |
| Document corpus | Low millions of chunks (pgvector HNSW practical limit, DEC-002) | Vector search latency degrades beyond `09_rag_performance.md`'s target; a dedicated vector DB becomes worth evaluating |
| Audit table size | No hard ceiling, but query performance on `19_audit_api.md` degrades without partitioning beyond tens of millions of rows | Partitioning `audit_events` by time range becomes a needed optimization (not yet designed for V1) |
| Concurrent code-execution sandboxes | ~5-10 (CPU/memory-bound on PROFILE-C) | Queue depth grows; consider dedicated sandbox-execution nodes in a multi-node design |

## Rule

These are not hard-coded application limits — they're the point at which the single-node
architecture's *practical* performance degrades below the targets in this directory, which is
the trigger for evaluating `later/08_multi_node_scaling.md`, gated on `REQ-DEP-004`'s pending
decision.
