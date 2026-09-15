"""Persistence stub for the documents store.

The canonical database is PostgreSQL (docs/06_TECHNOLOGY_STACK.md); it is not available in
this development environment, so per the dependency-graph rule this is an explicit stub:
an in-memory store with the exact interface the repository layer will implement against
SQLAlchemy/psycopg later. It never pretends to be durable — the module docstring and the
warn-once log say so, satisfying developer rule 7 (fail loud, not silent).

Transaction semantics: the feature docs require the documents write and the audit write to
be atomic ("steps 3-4 are atomic"). This store models that with record(id, audit_event)
pairs: an audit event is appended to the same record as the state change that produced it.
The audit events themselves go to the AuditSink given to the service, which is the same
InMemoryAuditSink in tests — the pairing is the stub-level guarantee; audit-service
enforces it at the database level when it lands.
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .domain import Document

logger = logging.getLogger("document_pipeline.store")

_WARNED = False


def _warn_once() -> None:
    global _WARNED
    if not _WARNED:
        logger.warning(
            "InMemoryDocumentStore active: documents are NOT persisted. Replace with the "
            "PostgreSQL repository (schemas/01_database_schema.md) — see DEC-023."
        )
        _WARNED = True


class ResourceConflict(Exception):
    """Optimistic-concurrency failure (maps to RESOURCE_CONFLICT at the handler layer)."""

    def __init__(self, doc_id: str, current_state: str, expected_state: str) -> None:
        super().__init__(
            f"document {doc_id} is in state {current_state}, expected {expected_state}"
        )
        self.current_state = current_state
        self.expected_state = expected_state


class InMemoryDocumentStore:
    def __init__(self) -> None:
        _warn_once()
        self._docs: Dict[str, Document] = {}
        self._audit_by_doc: Dict[str, List[dict]] = {}
        self._lock = threading.Lock()

    # -- reads --------------------------------------------------------------

    def get(self, doc_id: str) -> Optional[Document]:
        with self._lock:
            return self._docs.get(doc_id)

    def list_by_workspace(self, workspace_id: str) -> List[Document]:
        with self._lock:
            return [d for d in self._docs.values()
                    if d.workspace_id == workspace_id and d.deleted_at is None]

    def audit_events_for(self, doc_id: str) -> List[dict]:
        with self._lock:
            return list(self._audit_by_doc.get(doc_id, []))

    def append_audit(self, doc_id: str, event: dict) -> None:
        """Pair a non-transition audit event (e.g. the invocation event) with the row's
        audit trail — same logical transaction as the read/write it describes."""
        with self._lock:
            self._audit_by_doc.setdefault(doc_id, []).append(event)

    # -- writes (each takes the audit event emitted for the same logical operation) --

    def insert(self, doc: Document, audit_event: dict) -> Document:
        with self._lock:
            if doc.id in self._docs:
                raise ResourceConflict(doc.id, "exists", "absent")
            self._docs[doc.id] = doc
            self._audit_by_doc.setdefault(doc.id, []).append(audit_event)
            return doc

    def update_state(self, doc_id: str, expected_state: str, new_state: str,
                     audit_event: dict) -> Document:
        """CAS update: rejects when the row is no longer in expected_state (row-lock
        semantics per feature docs edge case: concurrent callers get 409, never a lost
        update)."""
        with self._lock:
            doc = self._docs.get(doc_id)
            if doc is None:
                raise KeyError(doc_id)
            if doc.state != expected_state:
                raise ResourceConflict(doc_id, doc.state, expected_state)
            doc.state = new_state
            self._audit_by_doc.setdefault(doc_id, []).append(audit_event)
            return doc

    def soft_delete(self, doc_id: str, audit_event: dict) -> None:
        with self._lock:
            doc = self._docs.get(doc_id)
            if doc is None:
                raise KeyError(doc_id)
            doc.deleted_at = doc.deleted_at or datetime.now(timezone.utc)
            self._audit_by_doc.setdefault(doc_id, []).append(audit_event)
