# Scaling Strategy

> How the system would scale beyond PROFILE-B, and which parts of V1's design already
> anticipate this (per DEC-001's stated rationale).

## Scaling dimensions

1. **Concurrent users** — bounded in V1 by PROFILE-B's single-GPU inference throughput; scaling
   this requires either more/bigger GPUs (PROFILE-C/D) or horizontal Inference Gateway
   replicas (`later/08_multi_node_scaling.md`), gated on `REQ-PERF-002`'s pending decision.
2. **Document corpus size** — pgvector's HNSW index scales into the millions of chunks
   (DEC-002's stated assumption); beyond that, a dedicated vector database becomes worth
   revisiting cost.
3. **Concurrent tasks** — bounded by Tool Gateway/sandbox container capacity; horizontal
   scaling of the Tool Gateway service is straightforward given its stateless design
   (`06_service_boundaries.md`) — the sandbox containers themselves are the actual constrained
   resource.

## What does NOT need to scale differently

The trust layer (Identity, Policy Engine, Audit) is lightweight per-request
(`runtime/11_retry_policy.md`'s `interactive-read` class, <10ms) and is not expected to be a
bottleneck at any scale this project anticipates — scaling effort should focus on the
capability layer, not the trust layer.
