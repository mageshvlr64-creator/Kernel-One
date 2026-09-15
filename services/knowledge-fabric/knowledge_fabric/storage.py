"""Dependency seams — explicit stubs per the dependency-graph rule (never silent fakes).

- DocumentSource: read-only view over document-pipeline's store. In production this is a
  documents API client / shared DB; here an in-process dict view with the same semantics
  (only INDEXING documents are indexable; non-existent documents are RESOURCE_NOT_FOUND —
  actually FILE_NOT_FOUND per registry — hmm, the registry's 404 code is FILE_NOT_FOUND;
  it is used for unknown document references, consistent with document-pipeline's usage).
- ChunkIndex: the chunks/embeddings store. Production: PostgreSQL + pgvector
  (integrations/05, 06: HNSW, cosine). Stub: in-memory lists + brute-force cosine
  similarity with the same result semantics.
- EmbeddingProvider: the model-inference seam (features/01). Stub: deterministic
  hash-based 768-dim vectors so retrieval behavior is real and testable without a model.

Replacement seams are constructor-injected (ops.take a store instance) — documented in
DEC-023's stub strategy.
"""
from __future__ import annotations

import hashlib
import math
from typing import Any, Dict, Iterable, List, Optional

from .domain import DocumentChunk, DocumentRef


class DocumentSource:
    """In-memory view of documents available for indexing."""

    def __init__(self) -> None:
        self._docs: Dict[str, DocumentRef] = {}

    def upsert(self, ref: DocumentRef) -> None:
        self._docs[ref.document_id] = ref

    def get(self, document_id: str) -> Optional[DocumentRef]:
        return self._docs.get(document_id)

    def list_by_state(self, state: str) -> List[DocumentRef]:
        return [d for d in self._docs.values() if d.state == state]


class ChunkIndex:
    """In-memory chunk/embedding store with brute-force cosine retrieval.

    Mirrors the semantics of the canonical pgvector design (HNSW index, cosine
    distance): order-only stability, deterministic scoring, classification filter
    applied before scoring (never queried without it — domain/07 Notes).
    """

    def __init__(self, embedding_dim: int = 768) -> None:
        self.embedding_dim = embedding_dim
        self._chunks: Dict[str, DocumentChunk] = {}
        self._removed: set = set()

    # ---- write path (indexing ops) -------------------------------------------------
    def replace_document_chunks(self, document_id: str,
                                chunks: List[DocumentChunk]) -> None:
        """Idempotent (re)indexing: existing chunks for the document are replaced."""
        self._chunks = {cid: c for cid, c in self._chunks.items()
                        if c.document_id != document_id}
        for c in chunks:
            self._chunks[c.id] = c
        self._removed.discard(document_id)

    def mark_document_removed(self, document_id: str) -> None:
        self._removed.add(document_id)

    def count_for_document(self, document_id: str) -> int:
        return sum(1 for c in self._chunks.values() if c.document_id == document_id)

    def chunks_for_document(self, document_id: str) -> List[DocumentChunk]:
        return sorted((c for c in self._chunks.values()
                       if c.document_id == document_id),
                      key=lambda c: c.chunk_index)

    # ---- read path (retrieval ops) --------------------------------------------------
    def all_chunks(self) -> List[DocumentChunk]:
        return list(self._chunks.values())

    def count_total(self) -> int:
        return len(self._chunks)


def cosine(a: List[float], b: List[float]) -> float:
    """Cosine similarity in [-1, 1]; zero vectors score 0.0 (no direction)."""
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def embed_text(text: str, dim: int = 768) -> List[float]:
    """Deterministic stub embedding: token-hash bag-of-words projected to `dim` dims.

    Real behavior for tests: similar texts (shared tokens) produce higher cosine
    similarity than unrelated texts. Replaced by the model-inference seam
    (features/01) in a later increment — DEC-023 stub strategy.
    """
    vec = [0.0] * dim
    for token in text.lower().split():
        h = int.from_bytes(hashlib.sha256(token.encode()).digest()[:8], "big")
        idx = h % dim
        sign = 1.0 if (h >> 63) & 1 == 0 else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec
