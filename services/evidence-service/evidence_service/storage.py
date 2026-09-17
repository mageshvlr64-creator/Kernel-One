"""Dependency seams — explicit stubs per the dependency-graph rule (never silent fakes).

- EvidenceLinks: this service's own store (feature docs §2 "the evidence_links
  store"). Production: PostgreSQL table per domain/13; stub: in-process dict.
- SourceChainStore: point-in-time document facts the chain resolves against
  (Document.version, sha256, authority, effective_from/effective_until per
  domain/06). Production: read-only documents API / shared DB view owned by
  document-pipeline; stub: seeded in-process view.
- RetrievalView: read-only view of knowledge-fabric's chunks for coordinate-
  level citation resolution (features/13 owns the chunk store). Stub: in-process.

Replacement seams are constructor-injected — DEC-023's stub strategy.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .domain import Citation, Evidence


class EvidenceLinks:
    """In-process evidence_links store (single-writer, insert-ordered)."""

    def __init__(self) -> None:
        self._evidence: Dict[str, Evidence] = {}
        self._citations: Dict[str, List[Citation]] = {}   # evidence_id -> citations
        self._by_task: Dict[str, List[str]] = {}

    def add(self, evidence: Evidence) -> Evidence:
        self._evidence[evidence.id] = evidence
        self._by_task.setdefault(evidence.task_id, []).append(evidence.id)
        return evidence

    def get(self, evidence_id: str) -> Optional[Evidence]:
        return self._evidence.get(evidence_id)

    def for_task(self, task_id: str) -> List[Evidence]:
        return [self._evidence[eid] for eid in self._by_task.get(task_id, [])]

    def set_verification_status(self, evidence_id: str, status: str) -> Optional[Evidence]:
        ev = self._evidence.get(evidence_id)
        if ev is not None:
            ev.verification_status = status
        return ev

    def add_citation(self, citation: Citation) -> Citation:
        self._citations.setdefault(citation.evidence_id, []).append(citation)
        return citation

    def citations_for(self, evidence_id: str) -> List[Citation]:
        return list(self._citations.get(evidence_id, []))

    def count(self) -> int:
        return len(self._evidence)


class SourceChainStore:
    """Point-in-time Document facts for chain resolution (stub of the documents API).

    `versions` maps document_id -> list of {version, sha256, authority,
    effective_from, effective_until, superseded_by}; newest version last.
    """

    def __init__(self) -> None:
        self._versions: Dict[str, List[Dict[str, Any]]] = {}

    def seed_document(self, document_id: str, version: int, sha256: str,
                      authority: str, effective_from: Optional[str] = None,
                      effective_until: Optional[str] = None) -> Dict[str, Any]:
        row = {"version": version, "sha256": sha256, "authority": authority,
               "effective_from": effective_from, "effective_until": effective_until}
        self._versions.setdefault(document_id, []).append(row)
        self._versions[document_id].sort(key=lambda r: r["version"])
        return row

    def version_row(self, document_id: str, version: int) -> Optional[Dict[str, Any]]:
        for row in self._versions.get(document_id, []):
            if row["version"] == version:
                return row
        return None

    def current_version(self, document_id: str) -> Optional[Dict[str, Any]]:
        rows = self._versions.get(document_id)
        return rows[-1] if rows else None

    def is_superseded(self, document_id: str, version: int) -> bool:
        rows = self._versions.get(document_id, [])
        return bool(rows) and version < rows[-1]["version"]


class RetrievalView:
    """Read-only chunk view for coordinate resolution (knowledge-fabric seam).

    Chunks: chunk_id -> {document_id, chunk_index, page_number, bbox, text}.
    """

    def __init__(self) -> None:
        self._chunks: Dict[str, Dict[str, Any]] = {}

    def seed_chunk(self, chunk_id: str, document_id: str, chunk_index: int,
                   page_number: Optional[int] = None,
                   bbox: Optional[List[float]] = None, text: str = "") -> Dict[str, Any]:
        row = {"document_id": document_id, "chunk_index": chunk_index,
               "page_number": page_number, "bbox": bbox, "text": text}
        self._chunks[chunk_id] = row
        return row

    def get(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        return self._chunks.get(chunk_id)
