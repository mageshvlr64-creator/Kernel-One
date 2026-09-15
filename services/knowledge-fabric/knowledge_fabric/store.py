"""In-memory store for knowledge-fabric's own resource state.

Tracks each document's indexing progress (chunk counts, embeddings filled, index
entries) so retrieval ops can fail closed when the index is unavailable rather than
returning degraded results silently.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from .domain import DocumentChunk, SearchHit


class KnowledgeStore:
    """Owns: per-document index records + the chunk index (via composition)."""

    def __init__(self, chunk_index: "ChunkIndex") -> None:
        from .storage import ChunkIndex as _CI  # local import avoids cycle in tests
        self.index = chunk_index if isinstance(chunk_index, _CI) else _CI()
        # document_id -> {"chunks": int, "embedded": int, "ready": bool,
        #                 "failed": Optional[str]}
        self.index_records: Dict[str, dict] = {}

    # ---- index bookkeeping ------------------------------------------------------------
    def record_chunks(self, document_id: str, count: int) -> None:
        rec = self.index_records.setdefault(document_id, {})
        rec["chunks"] = count

    def record_embedded(self, document_id: str, count: int) -> None:
        rec = self.index_records.setdefault(document_id, {"chunks": count})
        rec["embedded"] = count

    def record_ready(self, document_id: str, ready: bool) -> None:
        rec = self.index_records.setdefault(document_id, {})
        rec["ready"] = ready

    def record_failed(self, document_id: str, reason: str) -> None:
        rec = self.index_records.setdefault(document_id, {})
        rec["failed"] = reason
        rec["ready"] = False

    def get_record(self, document_id: str) -> Optional[dict]:
        return self.index_records.get(document_id)

    # ---- passthrough to the chunk index ------------------------------------------------
    def chunks_for_document(self, document_id: str) -> List[DocumentChunk]:
        return self.index.chunks_for_document(document_id)

    def search(self, hits: List[SearchHit]) -> List[SearchHit]:
        return hits
