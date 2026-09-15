"""Document entity — docs/domain/06_document_model.md (canonical field list) with the
wire enum values from docs/schemas/07_document_schema.md.

This service is the canonical owner/mutator of the Document entity per domain/06 (Document
Ingestion owns the UPLOADED->...->FAILED lifecycle states). Other components read it via
the API; they never write its table.

Not present until later increments: DocumentChunk rows (created during INDEXING by the
knowledge fabric, feature group 13). The knowledge-trust fields (authority,
effective_from, effective_until, superseded_by) are carried from day one per domain/06.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

MIME_ENUM = (
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain",
    "text/csv",
    "image/png",
    "image/jpeg",
)
CLASSIFICATION_ENUM = ("PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED")
STATE_ENUM = ("UPLOADED", "VALIDATING", "EXTRACTING", "OCR", "INDEXING",
              "READY", "FAILED", "DELETED")
AUTHORITY_ENUM = ("primary", "secondary", "reference")

MAX_FILENAME_LENGTH = 512  # docs/schemas/07_document_schema.md

_FILENAME_SAFE = re.compile(r"[^A-Za-z0-9._()\- ]+")


def new_document_id() -> str:
    return str(uuid.uuid4())


def sanitize_filename(name: str) -> str:
    """Sanitize an untrusted upload filename (docs/security/09_path_traversal.md).

    Strips any path components and control characters; the result is a bare display name,
    never used to build a filesystem path (storage keys come from the document id).
    """
    name = name.replace("\\", "/").split("/")[-1]
    name = name.replace("\x00", "")
    cleaned = _FILENAME_SAFE.sub("_", name).strip(". ")
    return cleaned[:MAX_FILENAME_LENGTH] or "upload"


@dataclass
class Document:
    """docs/domain/06_document_model.md. Defaults follow the canonical column defaults."""
    id: str
    workspace_id: str
    filename: str
    mime_type: str
    size_bytes: int
    sha256: str
    storage_uri: str
    classification: str = "INTERNAL"
    state: str = "UPLOADED"
    version: int = 1
    authority: str = "secondary"
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None
    superseded_by: Optional[str] = None
    uploaded_by: str = ""
    created_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.effective_from is None:
            # domain/06: effective_from defaults to created_at.
            self.effective_from = self.created_at
        if self.filename and len(self.filename) > MAX_FILENAME_LENGTH:
            raise ValueError("filename exceeds docs/schemas/07 maxLength 512")

    def to_dict(self) -> dict:
        """Wire shape per docs/schemas/07_document_schema.md (Document subset for API)."""
        return {
            "id": self.id,
            "filename": self.filename,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "classification": self.classification,
            "state": self.state,
            "version": self.version,
            "authority": self.authority,
            "effective_from": _iso(self.effective_from),
            "effective_until": _iso(self.effective_until),
            "superseded_by": self.superseded_by,
            "uploaded_by": self.uploaded_by,
            "workspace_id": self.workspace_id,
            "created_at": _iso(self.created_at),
        }


def _iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
