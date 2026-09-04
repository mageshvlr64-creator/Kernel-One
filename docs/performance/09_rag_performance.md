# RAG Performance

> Budgets specific to `features/13_knowledge_fabric/` retrieval, referenced by REQ-FUNC-004's
> acceptance criteria.

| Metric | Target | Provenance |
|---|---|---|
| Hybrid search (vector + keyword) over a 100k-chunk corpus | < 400ms (p95) | DESIGN LIMIT |
| Reranking step (`features/13_knowledge_fabric/10_reranking.md`) | < 200ms (p95) added latency | DESIGN LIMIT |
| Classification/workspace filter overhead (applied at query time, REQ-FUNC-004) | < 20ms added latency (filter is a query predicate, not a post-processing pass) | CONFIG DEFAULT |

## Scaling note

These targets assume PostgreSQL's HNSW index (DEC-002); if corpus size grows well beyond the
"tens of thousands of chunks" assumption in DEC-002, these targets should be re-measured, not
assumed to hold — see `architecture/14_scaling_strategy.md`.
