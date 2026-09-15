"""Operation handlers — the single implementation behind both the REST routes and the
feature-op routes (feature docs §12: "there is exactly one implementation, not two").

Guarantee structure:
- execute() is the one entry point. It dispatches to handle_<op>, then emits EXACTLY ONE
  `document_ingestion.<op>` audit event per invocation — success, error, or denial
  (feature §22). Handlers never emit the invocation event themselves; they only emit the
  canonical `document.*` state-transition events. This makes the "exactly one" invariant
  structural, not per-handler discipline.
- Permissions are enforced via the policy stub before any state is touched; denials are
  audited with result=denied and the denying rule (feature §16).
- Failures map to specific registry codes with specific reasons (failures/21: never a
  generic parse error).
- Pipeline scope (DEC-023): this increment applies UPLOADED -> VALIDATING -> EXTRACTING
  with real work behind each transition. EXTRACTING -> OCR and EXTRACTING -> INDEXING are
  computed (scanned_candidate) but NOT applied, because the side effects those
  transitions own (OCR recognition, chunk/embed/index) belong to feature groups 11 and 13
  which are later increments. Emitting document.ocr_completed / document.indexed without
  the work would misstate reality; the state machine guard already reserves those
  transitions for their canonical owners.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import audit as audit_mod
from . import pdf as pdf_mod
from . import statemachine as sm
from .config import Settings
from .domain import (AUTHORITY_ENUM, CLASSIFICATION_ENUM, Document, MIME_ENUM,
                     new_document_id, sanitize_filename)
from .errors import RegistryError
from .policy import Actor, enforce
from .retry import run_with_retry
from .store import InMemoryDocumentStore, ResourceConflict
from .storage import ObjectStorage

logger = logging.getLogger("document_pipeline.ops")

# Malware-signature stub (VALIDATING check). The canonical anti-malware integration is a
# later hardening item; this stub rejects the well-known EICAR test string and executable
# magic bytes so the check point exists and is testable. Documented DEC-023.
_MALWARE_SIGNATURES: Tuple[bytes, ...] = (
    b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*",
    b"MZ",       # Windows PE
    b"\x7fELF",  # Linux ELF
)

DENIAL_CODES = {"POLICY_DENIED", "TOOL_NOT_ALLOWED", "FILE_CLASSIFICATION_DENIED"}


@dataclass
class Context:
    """Per-invocation context. actor_id/workspace_id always come from the authenticated
    session (actor record), never from client-supplied body fields (feature docs §6)."""
    actor: Actor
    session_id: Optional[str] = None
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_ip: Optional[str] = None
    idempotency_key: Optional[str] = None
    source_interface: str = "api"


@dataclass
class HandlerOutcome:
    doc: Optional[Document] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    reason: Optional[str] = None  # human-readable detail for the audit event


@dataclass
class OpResult:
    """Feature-doc Outputs shape (§7)."""
    status: str
    resource_id: str
    state: str
    audit_event_id: str
    timestamp: str
    data: Dict[str, Any] = field(default_factory=dict)


class OpError(Exception):
    """Carrier for a handled RegistryError plus its correlation/audit ids, raised to the
    API layer after the invocation audit event has been emitted."""

    def __init__(self, err: RegistryError, correlation_id: str, audit_event_id: str) -> None:
        super().__init__(err.code)
        self.err = err
        self.correlation_id = correlation_id
        self.audit_event_id = audit_event_id


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class DocumentIngestionService:
    """Owns the dependencies; handlers below are pure orchestration over it."""

    def __init__(self, store: InMemoryDocumentStore, storage: ObjectStorage,
                 audit_sink: audit_mod.AuditSink, settings: Settings) -> None:
        self.store = store
        self.storage = storage
        self.audit = audit_sink
        self.settings = settings
        # Extraction cache: parsed pages per document id. Stub for the persistence the
        # knowledge fabric (group 13) will read from PostgreSQL later (DEC-023).
        self.extractions: Dict[str, pdf_mod.ParseOutcome] = {}

    # ------------------------------------------------------------------ audit helpers

    def _emit(self, event: Dict[str, Any]) -> None:
        """Emit to the audit sink; a sink failure fails the operation closed (feature §5:
        if the audit write cannot be guaranteed, the state change is rolled back)."""
        try:
            self.audit.emit(event)
        except Exception as exc:
            raise RegistryError("DEPENDENCY_UNAVAILABLE",
                                operator_detail=f"audit sink unavailable: {exc}") from exc

    def _invocation_event(self, ctx: Context, op: str, action: str, *, result: str,
                          doc: Optional[Document] = None, payload: Any = None,
                          error_code: Optional[str] = None, reason: Optional[str] = None,
                          decision: Optional[str] = None) -> Dict[str, Any]:
        return audit_mod.build_audit_event(
            event_type=f"document_ingestion.{op}",
            actor_id=ctx.actor.actor_id,
            action=action,
            resource_type="Document",
            result=result,
            resource_id=doc.id if doc else None,
            classification=doc.classification if doc else None,
            session_id=ctx.session_id,
            correlation_id=ctx.correlation_id,
            decision=decision,
            error_code=error_code,
            reason=reason,
            source_interface=ctx.source_interface,
            source_ip=ctx.source_ip,
            payload_hash=audit_mod.payload_hash(payload) if payload is not None else None,
        )

    def _transition_event(self, ctx: Context, event_type: str, doc: Document, *,
                          result: str, error_code: Optional[str] = None,
                          reason: Optional[str] = None) -> Dict[str, Any]:
        return audit_mod.build_audit_event(
            event_type=event_type,
            actor_id=ctx.actor.actor_id,
            action="update",
            resource_type="Document",
            result=result,
            resource_id=doc.id,
            classification=doc.classification,
            session_id=ctx.session_id,
            correlation_id=ctx.correlation_id,
            error_code=error_code,
            reason=reason,
            source_interface=ctx.source_interface,
            source_ip=ctx.source_ip,
        )

    def _apply_transition(self, ctx: Context, doc: Document, new_state: str, *,
                          canonical_event: str) -> None:
        """CAS state-machine transition + canonical transition event. If the audit emit
        fails the transition raises, leaving no unaudited state change (feature §5)."""
        sm.transition(doc.state, new_state, owner="document_ingestion")
        event = self._transition_event(ctx, canonical_event, doc, result="success")
        try:
            self.store.update_state(doc.id, doc.state, new_state, event)
        except ResourceConflict as exc:
            raise RegistryError(
                "RESOURCE_CONFLICT",
                operator_detail=f"document {doc.id}: {exc}",
            ) from exc
        doc.state = new_state
        self._emit(event)

    def _fail(self, ctx: Context, op: str, doc: Document, reason: str) -> None:
        """Move the document VALIDATING/EXTRACTING -> FAILED with a specific reason
        (failures/21), then raise INVALID_REQUEST — the dispatcher emits the invocation
        error event."""
        try:
            event = self._transition_event(ctx, "document.failed", doc, result="error",
                                           error_code="INVALID_REQUEST", reason=reason)
            self.store.update_state(doc.id, doc.state, "FAILED", event)
            doc.state = "FAILED"
            self._emit(event)
        except ResourceConflict as exc:
            raise RegistryError("RESOURCE_CONFLICT", operator_detail=str(exc)) from exc
        raise RegistryError("INVALID_REQUEST", operator_detail=reason)


# --------------------------------------------------------------------------- dispatcher

OPS: Dict[str, Dict[str, Any]] = {
    # op slug: {"handler": ..., "action": canonical audit action, "expected_state": state
    # the document must be in before the op runs (None = create path)}
    "upload_validation": {"handler": None, "action": "create", "expected_state": None},
    "file_type_detection": {"handler": None, "action": "execute", "expected_state": "UPLOADED"},
    "native_pdf_parsing": {"handler": None, "action": "execute", "expected_state": "EXTRACTING"},
    "scanned_pdf_detection": {"handler": None, "action": "execute", "expected_state": "EXTRACTING"},
    "page_extraction": {"handler": None, "action": "execute", "expected_state": None},
    "metadata_extraction": {"handler": None, "action": "execute", "expected_state": None},
    "ingestion_overview": {"handler": None, "action": "read", "expected_state": None},
}


def execute(service: DocumentIngestionService, ctx: Context, op: str,
            payload: Dict[str, Any]) -> OpResult:
    """The one entry point for every ingestion op (HTTP wrapper + internal callers).

    Emits exactly one `document_ingestion.<op>` audit event per invocation, success or
    failure, and raises OpError carrying the envelope-ready RegistryError on failure.
    """
    spec = OPS.get(op)
    if spec is None:
        raise RegistryError("INVALID_REQUEST", operator_detail=f"unknown op {op!r}")

    try:
        outcome = spec["handler"](service, ctx, payload)  # type: ignore[misc]
    except RegistryError as err:
        denied = err.code in DENIAL_CODES
        event = service._invocation_event(
            ctx, op, spec["action"],
            result="denied" if denied else "error",
            doc=None, payload=payload,
            error_code=err.code,
            reason=err.operator_detail or err.user_message,
            decision="denied" if denied else None,
        )
        service._emit(event)
        err.correlation_id = ctx.correlation_id
        raise OpError(err, ctx.correlation_id, event["event_id"]) from err

    event = service._invocation_event(
        ctx, op, spec["action"], result="success",
        doc=outcome.doc, payload=payload, reason=outcome.reason, decision="allowed",
    )
    service._emit(event)
    if outcome.doc is not None:
        service.store.append_audit(outcome.doc.id, event)
    return OpResult(
        status="ok",
        resource_id=outcome.doc.id if outcome.doc else "",
        state=outcome.doc.state if outcome.doc else "",
        audit_event_id=event["event_id"],
        timestamp=_now_iso(),
        data=outcome.extra,
    )


# ---------------------------------------------------------------------------
# upload_validation — feature file 02 (+ REST POST /api/v1/documents, api/11)
# ---------------------------------------------------------------------------

def handle_upload_validation(service: DocumentIngestionService, ctx: Context,
                             payload: Dict[str, Any]) -> HandlerOutcome:
    """Validate the upload, store the file, create the Document row in state UPLOADED.

    Dedup per docs/runtime/15_idempotency.md: Document upload is deduplicated by sha256
    regardless of Idempotency-Key. Dedup returns the original document; this invocation
    still gets its own audit event from the dispatcher.
    """
    field_errors: List[Dict[str, str]] = []
    if not isinstance(payload, dict) or not payload:
        raise RegistryError("INVALID_REQUEST", details=[{"field": "payload",
                                                         "message": "payload is required"}])

    filename = payload.get("filename")
    if not isinstance(filename, str) or not filename.strip():
        field_errors.append({"field": "filename", "message": "filename is required"})
    content_b64 = payload.get("content_base64")
    if not isinstance(content_b64, str) or not content_b64:
        field_errors.append({"field": "content_base64", "message": "content_base64 is required"})
    classification = payload.get("classification", "INTERNAL")
    if classification not in CLASSIFICATION_ENUM:
        field_errors.append({"field": "classification",
                             "message": "must be one of PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED"})
    authority = payload.get("authority", "secondary")
    if authority not in AUTHORITY_ENUM:
        field_errors.append({"field": "authority",
                             "message": "must be one of primary, secondary, reference"})
    if field_errors:
        raise RegistryError("INVALID_REQUEST", details=field_errors)
    assert filename is not None and content_b64 is not None

    # Permission check BEFORE any state is touched (feature §16).
    enforce("Document", "create", ctx.actor,
            resource_classification=classification,
            resource_workspace_id=ctx.actor.workspace_id)

    try:
        content = base64.b64decode(content_b64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise RegistryError("INVALID_REQUEST", details=[{
            "field": "content_base64", "message": "not valid base64"}]) from exc

    if len(content) < 1:
        raise RegistryError("INVALID_REQUEST", details=[{
            "field": "content_base64", "message": "file is empty"}])
    if len(content) > service.settings.max_upload_size_bytes:
        # api/11: size <= 200MB (MAX_UPLOAD_SIZE_BYTES) or INVALID_REQUEST.
        raise RegistryError("INVALID_REQUEST", details=[{
            "field": "content", "message": "file exceeds the maximum upload size"}])

    detected = detect_mime(content)
    if detected is None:
        # Reject before any state is touched (feature §30 edge case). The deeper
        # VALIDATING checks (malware signatures) remain file_type_detection's job.
        raise RegistryError("INVALID_REQUEST",
                            operator_detail="file content does not match any supported type")
    if detected == "text/plain":
        decoded = content.decode("utf-8", errors="replace")
        detected = refine_text_mime(content, decoded)

    sha256 = hashlib.sha256(content).hexdigest()

    # sha256 dedup within the workspace (runtime/15).
    for existing in service.store.list_by_workspace(ctx.actor.workspace_id):
        if existing.sha256 == sha256:
            return HandlerOutcome(
                doc=existing, extra={"deduplicated": True},
                reason="duplicate content deduplicated by sha256 (runtime/15)")

    doc_id = new_document_id()
    doc = Document(
        id=doc_id,
        workspace_id=ctx.actor.workspace_id,
        filename=sanitize_filename(filename),
        mime_type=detected,
        size_bytes=len(content),
        sha256=sha256,
        storage_uri=f"stub://object-storage/{doc_id}",
        classification=classification,
        state="UPLOADED",
        authority=authority,
        uploaded_by=ctx.actor.actor_id,
    )

    # Object storage put is the dependency call: document-processing retry class
    # (runtime/11: retryable on DEPENDENCY_UNAVAILABLE, 1 retry, fixed 2s backoff).
    # Raw dependency exceptions are translated to the registry code first, so the retry
    # rule (which applies to registry codes) governs the actual retry behavior.
    def _put() -> None:
        try:
            service.storage.put(doc_id, content)
        except RegistryError:
            raise
        except Exception as exc:
            raise RegistryError("DEPENDENCY_UNAVAILABLE",
                                operator_detail=f"object storage unavailable: {exc}") from exc

    run_with_retry(_put)

    transition_event = service._transition_event(ctx, "document.uploaded", doc,
                                                 result="success")
    try:
        service.store.insert(doc, transition_event)
    except ResourceConflict as exc:
        raise RegistryError("RESOURCE_CONFLICT", operator_detail=str(exc)) from exc
    service._emit(transition_event)
    return HandlerOutcome(doc=doc, extra={})


# ---------------------------------------------------------------------------
# file_type_detection — feature file 03
# ---------------------------------------------------------------------------

def handle_file_type_detection(service: DocumentIngestionService, ctx: Context,
                               payload: Dict[str, Any]) -> HandlerOutcome:
    """UPLOADED -> VALIDATING (deep content checks: signatures) -> EXTRACTING on success,
    or VALIDATING -> FAILED on a signature hit (canonical machine owner: Document
    Ingestion)."""
    doc = _load_doc(service, ctx, payload, action="execute", op="file_type_detection")

    content = _get_content(service, doc)
    service._apply_transition(ctx, doc, "VALIDATING", canonical_event="document.validated")

    for sig in _MALWARE_SIGNATURES:
        if content[:65536].find(sig) != -1:
            service._fail(ctx, "file_type_detection", doc,
                          "potential executable or malware signature detected")

    service._apply_transition(ctx, doc, "EXTRACTING", canonical_event="document.extracted")
    return HandlerOutcome(doc=doc, extra={})


# ---------------------------------------------------------------------------
# native_pdf_parsing — feature file 04 (PyMuPDF, integrations/09)
# ---------------------------------------------------------------------------

def handle_native_pdf_parsing(service: DocumentIngestionService, ctx: Context,
                              payload: Dict[str, Any]) -> HandlerOutcome:
    doc = _load_doc(service, ctx, payload, action="execute", op="native_pdf_parsing",
                    expected_state="EXTRACTING")
    if doc.mime_type != "application/pdf":
        raise RegistryError("INVALID_REQUEST",
                            operator_detail="native PDF parsing requires a PDF document")

    content = _get_content(service, doc)
    outcome = _parse_or_fail(service, ctx, doc, content)
    service.extractions[doc.id] = outcome

    route = "OCR" if outcome.scanned_candidate else "INDEXING"
    # Routing is computed here; the transition itself belongs to feature groups 11/13
    # (see module docstring: pipeline scope, DEC-023).
    return HandlerOutcome(
        doc=doc,
        extra={"page_count": outcome.page_count, "scanned_candidate": outcome.scanned_candidate,
               "routed_to": route, "transition_applied": False},
        reason=f"parsed {outcome.page_count} pages; routed to {route} "
               "(transition deferred to feature group 11/13)",
    )


# ---------------------------------------------------------------------------
# scanned_pdf_detection — feature file 05
# ---------------------------------------------------------------------------

def handle_scanned_pdf_detection(service: DocumentIngestionService, ctx: Context,
                                 payload: Dict[str, Any]) -> HandlerOutcome:
    doc = _load_doc(service, ctx, payload, action="execute", op="scanned_pdf_detection",
                    expected_state="EXTRACTING")
    if doc.mime_type != "application/pdf":
        raise RegistryError("INVALID_REQUEST",
                            operator_detail="scanned detection requires a PDF document")

    content = _get_content(service, doc)
    outcome = _parse_or_fail(service, ctx, doc, content)
    service.extractions[doc.id] = outcome

    empty_pages = [p.page_number for p in outcome.pages if p.text_empty]
    return HandlerOutcome(
        doc=doc,
        extra={"scanned": outcome.scanned_candidate, "page_count": outcome.page_count,
               "text_empty_pages": empty_pages},
        reason="scanned" if outcome.scanned_candidate else "native text layer present",
    )


# ---------------------------------------------------------------------------
# page_extraction — feature file 06
# ---------------------------------------------------------------------------

def handle_page_extraction(service: DocumentIngestionService, ctx: Context,
                           payload: Dict[str, Any]) -> HandlerOutcome:
    doc = _load_doc(service, ctx, payload, action="execute", op="page_extraction")
    content = _get_content(service, doc)

    if doc.state == "FAILED":
        # A prior parse moved the document to FAILED (failures/21); there is no
        # successful extraction to report — do not re-parse, return row-level truth.
        return HandlerOutcome(doc=doc, extra={"pages": [], "total_characters": 0,
                                              "parse_failed": True},
                              reason="document FAILED; no successful extraction")

    if doc.mime_type == "application/pdf":
        outcome = service.extractions.get(doc.id)
        if outcome is None:
            outcome = _parse_or_fail(service, ctx, doc, content)
            service.extractions[doc.id] = outcome
        pages = [{"page_number": p.page_number, "characters": len(p.text.strip()),
                  "has_images": p.has_images, "table_count": len(p.tables)}
                 for p in outcome.pages]
        total = sum(p["characters"] for p in pages)
    else:
        text = _decode_text(content)
        pages = [{"page_number": 1, "characters": len(text.strip()),
                  "has_images": False, "table_count": 0}]
        total = len(text.strip())

    return HandlerOutcome(doc=doc, extra={"pages": pages, "total_characters": total})


# ---------------------------------------------------------------------------
# metadata_extraction — feature file 07
# ---------------------------------------------------------------------------

def handle_metadata_extraction(service: DocumentIngestionService, ctx: Context,
                               payload: Dict[str, Any]) -> HandlerOutcome:
    doc = _load_doc(service, ctx, payload, action="execute", op="metadata_extraction")
    content = _get_content(service, doc)

    metadata: Dict[str, Any] = {
        "filename": doc.filename,
        "mime_type": doc.mime_type,
        "size_bytes": doc.size_bytes,
        "sha256": doc.sha256,
        "classification": doc.classification,
        "authority": doc.authority,
        "version": doc.version,
        "state": doc.state,
    }
    if doc.state == "FAILED":
        # Prior parse failed (failures/21): report row-level metadata only, no re-parse.
        metadata["parse_failed"] = True
        return HandlerOutcome(doc=doc, extra={"metadata": metadata},
                              reason="document FAILED; row-level metadata only")
    if doc.mime_type == "application/pdf":
        outcome = service.extractions.get(doc.id)
        if outcome is None:
            outcome = _parse_or_fail(service, ctx, doc, content)
            service.extractions[doc.id] = outcome
        metadata.update({
            "page_count": outcome.page_count,
            "table_count": sum(len(p.tables) for p in outcome.pages),
            "pages_with_images": sum(1 for p in outcome.pages if p.has_images),
            "text_characters": sum(len(p.text) for p in outcome.pages),
            "scanned_candidate": outcome.scanned_candidate,
        })
    else:
        text = _decode_text(content)
        metadata.update({
            "line_count": text.count("\n") + (1 if text and not text.endswith("\n") else 0),
            "text_characters": len(text),
        })

    return HandlerOutcome(doc=doc, extra={"metadata": metadata})


# ---------------------------------------------------------------------------
# ingestion_overview — feature file 01 (action: read)
# ---------------------------------------------------------------------------

def handle_ingestion_overview(service: DocumentIngestionService, ctx: Context,
                              payload: Dict[str, Any]) -> HandlerOutcome:
    doc = _load_doc(service, ctx, payload, action="read", op="ingestion_overview")
    stages = {
        "uploaded": True,
        "validated_or_later": doc.state not in ("UPLOADED",),
        "extracting_or_later": doc.state in ("EXTRACTING", "OCR", "INDEXING", "READY"),
        "ocr_routed": doc.state == "OCR" or (
            doc.id in service.extractions and service.extractions[doc.id].scanned_candidate),
        "ready": doc.state == "READY",
        "failed": doc.state == "FAILED",
    }
    return HandlerOutcome(doc=doc, extra={"stages": stages, "version": doc.version})


# --------------------------------------------------------------------------- helpers

OPS["upload_validation"]["handler"] = handle_upload_validation
OPS["file_type_detection"]["handler"] = handle_file_type_detection
OPS["native_pdf_parsing"]["handler"] = handle_native_pdf_parsing
OPS["scanned_pdf_detection"]["handler"] = handle_scanned_pdf_detection
OPS["page_extraction"]["handler"] = handle_page_extraction
OPS["metadata_extraction"]["handler"] = handle_metadata_extraction
OPS["ingestion_overview"]["handler"] = handle_ingestion_overview


def _load_doc(service: DocumentIngestionService, ctx: Context, payload: Dict[str, Any],
              *, action: str, op: str, expected_state: Optional[str] = None) -> Document:
    """Load + permission-check (+ state-check) the target document."""
    if not isinstance(payload, dict):
        raise RegistryError("INVALID_REQUEST", details=[{"field": "payload",
                                                         "message": "payload must be an object"}])
    doc_id = payload.get("document_id")
    if not isinstance(doc_id, str) or not doc_id:
        raise RegistryError("INVALID_REQUEST", details=[{
            "field": "document_id", "message": "document_id is required"}])
    try:
        uuid.UUID(doc_id)
    except ValueError as exc:
        raise RegistryError("INVALID_REQUEST", details=[{
            "field": "document_id", "message": "document_id must be a uuid"}]) from exc

    doc = service.store.get(doc_id)
    if doc is None or doc.deleted_at is not None:
        raise RegistryError("FILE_NOT_FOUND",
                            operator_detail=f"document {doc_id} not found")

    enforce("Document", action, ctx.actor,
            resource_classification=doc.classification,
            resource_workspace_id=doc.workspace_id,
            resource_owner_id=doc.uploaded_by)

    expected = OPS[op].get("expected_state") if op in OPS else expected_state
    if expected is not None and doc.state != expected:
        # Ops run in pipeline order; a mismatched state is a state conflict (canonical
        # machine: illegal operation against the current state -> RESOURCE_CONFLICT).
        raise RegistryError("RESOURCE_CONFLICT",
                            operator_detail=f"document is in state {doc.state}, "
                                            f"op requires {expected}")
    return doc


def _get_content(service: DocumentIngestionService, doc: Document) -> bytes:
    try:
        return service.storage.get(doc.id)
    except KeyError as exc:
        raise RegistryError("DEPENDENCY_UNAVAILABLE",
                            operator_detail="object content missing for document") from exc


def _parse_or_fail(service: DocumentIngestionService, ctx: Context, doc: Document,
                   content: bytes) -> pdf_mod.ParseOutcome:
    try:
        return pdf_mod.parse_pdf(content)
    except pdf_mod.PdfParseError as exc:
        # failures/21_pdf_failures.md: specific reason, INVALID_REQUEST, state FAILED.
        service._fail(ctx, "parse", doc, exc.reason)
        raise  # unreachable; _fail always raises


def detect_mime(data: bytes) -> Optional[str]:
    """Server-side content sniffing. domain/06: mime_type is detected server-side, never
    trusted from the client header. Returns a MIME_ENUM value or None."""
    if data.startswith(b"%PDF-"):
        return "application/pdf"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"PK\x03\x04"):
        head = data[:4096].lower()
        if b"word/" in head:
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if b"xl/" in head:
            return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if b"ppt/" in head:
            return "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        return None  # a zip that is not one of the three OOXML types is not accepted
    try:
        data[:4096].decode("utf-8")
    except UnicodeDecodeError:
        return None
    if b"\x00" in data[:4096]:
        return None
    return "text/plain"


def _looks_like_csv(text: str) -> bool:
    lines = [ln for ln in text.splitlines()[:10] if ln.strip()]
    if len(lines) < 2:
        return False
    return sum(1 for ln in lines if "," in ln) / len(lines) >= 0.6


def refine_text_mime(data: bytes, decoded: str) -> str:
    return "text/csv" if _looks_like_csv(decoded) else "text/plain"


def _decode_text(content: bytes) -> str:
    for encoding in ("utf-8", "cp1252"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise RegistryError("INVALID_REQUEST",
                        operator_detail="text file is not valid UTF-8 or CP1252")
