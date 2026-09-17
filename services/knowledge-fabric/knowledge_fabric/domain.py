"""Domain objects — canonical shapes from docs/domain/07_knowledge_model.md and
docs/schemas/08_chunk_schema.md (read-only contracts; this module implements them).

DocumentChunk required fields: id, document_id, chunk_index, text, embedding (exactly
768 floats per the canonical schema — validated here, rejecting with INVALID_REQUEST
field errors before any business logic). Optional: page_number, bbox (4 floats),
ocr_confidence (0..1).

KnowledgeIndex is this service's resource view of a Document's indexing state — it is
NOT a new state machine: the canonical Document machine (runtime/_state_machines_canonical)
stays the single source; this service triggers only its owner-legal transitions
INDEXING->READY (event document.indexed) and INDEXING->FAILED.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def validate_embedding(raw: Any, dim: int,
                       errors: List[Dict[str, str]]) -> None:
    if not isinstance(raw, list) or len(raw) != dim or \
            not all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in raw):
        errors.append({
            "field": "embedding",
            "issue": f"must be an array of exactly {dim} numbers",
        })


def validate_chunk_fields(payload: Dict[str, Any], *, dim: int,
                          errors: List[Dict[str, str]]) -> None:
    """Field-level validation shared by all chunk-creating ops (schemas/08)."""
    text = payload.get("text")
    if not isinstance(text, str) or not text.strip():
        errors.append({"field": "text", "issue": "required non-empty string"})
    ci = payload.get("chunk_index")
    if not isinstance(ci, int) or isinstance(ci, bool) or ci < 0:
        errors.append({"field": "chunk_index", "issue": "required integer >= 0"})
    if "embedding" in payload:
        validate_embedding(payload.get("embedding"), dim, errors)
    bbox = payload.get("bbox")
    if bbox is not None and (not isinstance(bbox, list) or len(bbox) != 4 or
                             not all(isinstance(x, (int, float)) for x in bbox)):
        errors.append({"field": "bbox", "issue": "must be [x0, y0, x1, y1] numbers"})
    oc = payload.get("ocr_confidence")
    if oc is not None and (not isinstance(oc, (int, float)) or not 0.0 <= oc <= 1.0):
        errors.append({"field": "ocr_confidence", "issue": "must be within 0..1"})


@dataclass
class DocumentChunk:
    document_id: str
    chunk_index: int
    text: str
    embedding: Optional[List[float]] = None   # None until embeddings op fills it
    page_number: Optional[int] = None
    bbox: Optional[Tuple[float, float, float, float]] = None
    ocr_confidence: Optional[float] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=now_iso)

    def to_dict(self, *, include_embedding: bool = False) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "id": self.id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "page_number": self.page_number,
            "bbox": list(self.bbox) if self.bbox else None,
            "text": self.text,
            "ocr_confidence": self.ocr_confidence,
            "created_at": self.created_at,
        }
        if include_embedding:
            out["embedding"] = self.embedding
        return out


@dataclass
class DocumentRef:
    """Read-only view of a Document, as consumed from document-pipeline's store."""
    document_id: str
    state: str                     # canonical Document state (must be INDEXING to index)
    workspace_id: str
    classification: str            # inherited by every chunk (domain/07 Notes)
    owner_id: str
    source_text: str               # extracted text to chunk (from page extraction)
    pages: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SearchHit:
    """One retrieval result (features/13 §09/§10/§12/§13)."""
    chunk_id: str
    document_id: str
    document_name: str
    chunk_index: int
    page_number: Optional[int]
    text: str
    score: float
    score_breakdown: Dict[str, float] = field(default_factory=dict)


@dataclass
class ContextBundle:
    """Assembled context (features/13 §13 context_assembly)."""
    query: str
    items: List[SearchHit]
    total_tokens_approx: int
    truncated: bool
    document_ids: List[str]
