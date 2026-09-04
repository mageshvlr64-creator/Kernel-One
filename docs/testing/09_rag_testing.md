# RAG Testing

> Covers `features/13_knowledge_fabric/` — retrieval accuracy and permission filtering.

## Required tests

- `TEST-RAG-003`: hybrid search (vector + keyword) returns relevant chunks for a known query
  against a fixed test corpus, and permission filtering excludes chunks from a document above
  the test caller's clearance — this is also `SEC-TEST-001`'s retrieval-layer verification.
- Reranking (`features/13_knowledge_fabric/10_reranking.md`) improves ranking quality on a
  fixed evaluation set, or gracefully degrades to pre-rerank ordering if the reranker is
  unavailable (`failures/26_reranker_failures.md`).
