"""Domain objects — canonical shapes from docs/domain/13_evidence_model.md,
docs/schemas/09_evidence_schema.md and docs/schemas/10_citation_schema.md
(read-only contracts; this module implements them).

Evidence required fields (domain/13): id, task_id, source_document_id,
document_version, chunk_id, source_hash, retrieval_method, source_authority,
verification_status, created_at. Optional: page_number, section_reference,
confidence (0.0–1.0). document_version/source_hash/source_authority are
denormalized from the Document row **at retrieval time** — point-in-time
correctness (domain/13 field notes).

Citation (schemas/10): {evidence_id, text_span_start, text_span_end} — the
rendered form of an Evidence record attached to a span of agent output.

`confidence` is the retriever's ranking signal, NEVER displayed as a bare
correctness probability (domain/13 methodology; master prompt §12 anti-pattern).
`verification_status` is written by the verification pipeline (op 09) — this
service never lets a caller set it directly on create.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

RETRIEVAL_METHODS = ("vector", "keyword", "hybrid")
SOURCE_AUTHORITIES = ("primary", "secondary", "reference")
VERIFICATION_STATUSES = ("unverified", "supported", "contradicted", "unsupported")

SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def is_uuid(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        uuid.UUID(value)
    except (ValueError, AttributeError):
        return False
    return True


def validate_evidence_fields(evidence: Dict[str, Any],
                             errors: List[Dict[str, str]]) -> None:
    """Field-level validation shared by all evidence-creating ops (schemas/09)."""
    if not is_uuid(evidence.get("task_id")):
        errors.append({"field": "task_id", "issue": "required uuid"})
    if not is_uuid(evidence.get("source_document_id")):
        errors.append({"field": "source_document_id", "issue": "required uuid (FK Document.id)"})
    if not is_uuid(evidence.get("chunk_id")):
        errors.append({"field": "chunk_id", "issue": "required uuid (FK DocumentChunk.id)"})
    dv = evidence.get("document_version")
    if not isinstance(dv, int) or isinstance(dv, bool) or dv < 1:
        errors.append({"field": "document_version", "issue": "required integer >= 1"})
    sh = evidence.get("source_hash")
    if not isinstance(sh, str) or not SHA256_RE.match(sh):
        errors.append({"field": "source_hash", "issue": "required 64-char lowercase hex sha256"})
    if evidence.get("retrieval_method") not in RETRIEVAL_METHODS:
        errors.append({"field": "retrieval_method",
                       "issue": f"one of {list(RETRIEVAL_METHODS)}"})
    if evidence.get("source_authority") not in SOURCE_AUTHORITIES:
        errors.append({"field": "source_authority",
                       "issue": f"one of {list(SOURCE_AUTHORITIES)}"})
    vs = evidence.get("verification_status", "unverified")
    if vs not in VERIFICATION_STATUSES:
        errors.append({"field": "verification_status",
                       "issue": f"one of {list(VERIFICATION_STATUSES)}"})
    page = evidence.get("page_number")
    if page is not None and (not isinstance(page, int) or isinstance(page, bool) or page < 1):
        errors.append({"field": "page_number", "issue": "integer >= 1 when present"})
    conf = evidence.get("confidence")
    if conf is not None and (not isinstance(conf, (int, float)) or isinstance(conf, bool)
                             or not 0.0 <= float(conf) <= 1.0):
        errors.append({"field": "confidence", "issue": "number within 0..1"})


def validate_citation_fields(citation: Dict[str, Any],
                             errors: List[Dict[str, str]]) -> None:
    """Field-level validation per schemas/10_citation_schema.md."""
    if not is_uuid(citation.get("evidence_id")):
        errors.append({"field": "evidence_id", "issue": "required uuid (FK Evidence.id)"})
    start = citation.get("text_span_start")
    end = citation.get("text_span_end")
    if not isinstance(start, int) or isinstance(start, bool) or start < 0:
        errors.append({"field": "text_span_start", "issue": "required integer >= 0"})
    if not isinstance(end, int) or isinstance(end, bool) or end < 0:
        errors.append({"field": "text_span_end", "issue": "required integer >= 0"})
    if isinstance(start, int) and isinstance(end, int) and not isinstance(start, bool) \
            and not isinstance(end, bool) and end < start:
        errors.append({"field": "text_span_end", "issue": "must be >= text_span_start"})


@dataclass
class Evidence:
    """One Evidence row (domain/13) — the proof a claim came from a source."""
    task_id: str
    source_document_id: str
    document_version: int
    chunk_id: str
    source_hash: str
    retrieval_method: str
    source_authority: str
    verification_status: str = "unverified"
    page_number: Optional[int] = None
    section_reference: Optional[str] = None
    confidence: Optional[float] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=now_iso)

    def to_dict(self, *, include_raw_confidence: bool = False) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "id": self.id,
            "task_id": self.task_id,
            "source_document_id": self.source_document_id,
            "document_version": self.document_version,
            "chunk_id": self.chunk_id,
            "page_number": self.page_number,
            "section_reference": self.section_reference,
            "source_hash": self.source_hash,
            "retrieval_method": self.retrieval_method,
            "source_authority": self.source_authority,
            "verification_status": self.verification_status,
            "created_at": self.created_at,
        }
        # domain/13: the raw retrieval score is a ranking signal, exposed only in a
        # clearly-labeled operator/debug view — never as a user-facing probability.
        if include_raw_confidence:
            out["confidence_ranking_signal"] = self.confidence
        return out


@dataclass
class Citation:
    """Inline citation pointer (schemas/10) — rendered Evidence on a text span."""
    evidence_id: str
    text_span_start: int
    text_span_end: int

    def to_dict(self) -> Dict[str, Any]:
        return {"evidence_id": self.evidence_id,
                "text_span_start": self.text_span_start,
                "text_span_end": self.text_span_end}
