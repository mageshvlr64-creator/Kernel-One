"""OCR ops layer — the nine feature ops of docs/features/11_ocr/.

Lives inside document-pipeline per 15_CODEBASE_TARGET_STRUCTURE.md (feature group 11 is
homed here), implemented against the same dispatcher pattern as the ingestion ops:
exactly one `ocr.<op>` invocation audit event per call (success, denial, or error),
registry-only error codes, and the canonical state-machine transitions owned by OCR
(OCR -> INDEXING with `document.ocr_completed`, OCR -> FAILED with `document.failed`).

Pipeline position: document-pipeline's scanned_pdf_detection reports scanned candidates;
the ingestion ops deliberately defer the EXTRACTING -> OCR transition to THIS module's
page_processing op (feature 04), which renders pages, recognizes text, reconstructs
document text, and completes with the OCR -> INDEXING hand-off to knowledge-fabric (#16).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import pdf as pdf_mod
from . import statemachine as sm
from .audit import build_audit_event
from .domain import Document
from .errors import RegistryError
from .ocr import (LOW_CONFIDENCE_THRESHOLD, OcrEngine, OcrPageResult,
                  engine_from_settings)
from .ops import Context, DocumentIngestionService, HandlerOutcome, OpError, _get_content
from .policy import enforce

DENIAL_CODES = {"AUTH_REQUIRED", "POLICY_DENIED", "TOOL_NOT_ALLOWED",
                "FILE_CLASSIFICATION_DENIED"}


@dataclass
class OcrPagesStore:
    """ocr_pages resource — one record per page (feature docs: `ocr_pages` store).

    Stub for the PostgreSQL table the schema pins; in-memory keyed by document id.
    Records: {"page_number", "text", "bbox_regions", "ocr_confidence",
    "low_confidence", "engine", "flagged_reason"}.
    """

    def __init__(self) -> None:
        self._pages: Dict[str, List[dict]] = {}

    def replace_document(self, doc_id: str, pages: List[dict]) -> None:
        self._pages[doc_id] = pages

    def get(self, doc_id: str) -> List[dict]:
        return list(self._pages.get(doc_id, []))

    def has(self, doc_id: str) -> bool:
        return doc_id in self._pages


@dataclass
class OcrOpResult:
    status: str
    resource_id: str
    state: str
    audit_event_id: str
    timestamp: str
    data: Dict[str, Any] = field(default_factory=dict)


class OcrService:
    """OCR feature-group service sharing document-pipeline's store/storage/audit."""

    def __init__(self, pipeline: DocumentIngestionService, *,
                 engine: Optional[OcrEngine] = None, use_paddle: bool = False) -> None:
        self.pipeline = pipeline
        self.store = pipeline.store
        self.audit = pipeline.audit
        self.settings = pipeline.settings
        self.pages = OcrPagesStore()
        self.engine = engine or engine_from_settings(use_paddle=use_paddle)

    # ---- helpers ---------------------------------------------------------------------
    def _invocation_event(self, ctx: Context, op: str, action: str, *, result: str,
                          doc: Optional[Document] = None, error_code: Optional[str] = None,
                          reason: Optional[str] = None) -> dict:
        return build_audit_event(
            event_type=f"ocr.{op}", actor_id=ctx.actor.actor_id, action=action,
            resource_type="Document", result=result,
            resource_id=doc.id if doc else None,
            classification=doc.classification if doc else None,
            session_id=ctx.session_id, correlation_id=ctx.correlation_id,
            error_code=error_code, reason=reason,
            source_interface=ctx.source_interface, source_ip=ctx.source_ip)

    def _emit(self, event: dict) -> None:
        try:
            self.audit.emit(event)
        except Exception as exc:
            raise RegistryError("DEPENDENCY_UNAVAILABLE",
                                operator_detail=f"audit sink unavailable: {exc}") from exc

    def _transition_event(self, ctx: Context, event_type: str, doc: Document, *,
                          result: str, reason: Optional[str] = None) -> dict:
        return build_audit_event(
            event_type=event_type, actor_id=ctx.actor.actor_id, action="update",
            resource_type="Document", result=result, resource_id=doc.id,
            classification=doc.classification, session_id=ctx.session_id,
            correlation_id=ctx.correlation_id, reason=reason,
            source_interface=ctx.source_interface, source_ip=ctx.source_ip)

    def _apply_transition(self, ctx: Context, doc: Document, new_state: str, *,
                          canonical_event: str, reason: Optional[str] = None) -> None:
        """OCR-owned transition (OCR -> INDEXING / OCR -> FAILED), CAS-guarded."""
        sm.transition(doc.state, new_state, owner="ocr")
        event = self._transition_event(ctx, canonical_event, doc, result="success",
                                       reason=reason)
        try:
            self.store.update_state(doc.id, doc.state, new_state, event)
        except Exception as exc:
            raise RegistryError("RESOURCE_CONFLICT",
                                operator_detail=f"document {doc.id}: {exc}") from exc
        doc.state = new_state
        self._emit(event)

    def _load_doc(self, ctx: Context, op: str, payload: Any, *,
                  action: str, expected_state: Optional[str]) -> Document:
        from .ops import OPS as INGEST_OPS
        if not isinstance(payload, dict):
            raise RegistryError("INVALID_REQUEST",
                                operator_detail="payload must be an object")
        doc_id = payload.get("document_id")
        if not isinstance(doc_id, str) or not doc_id:
            raise RegistryError("INVALID_REQUEST",
                                details=[{"field": "document_id",
                                          "issue": "document_id is required"}],
                                operator_detail="document_id required")
        try:
            uuid.UUID(doc_id)
        except ValueError:
            raise RegistryError("INVALID_REQUEST",
                                details=[{"field": "document_id",
                                          "issue": "document_id must be a uuid"}],
                                operator_detail="document_id must be a uuid")
        doc = self.store.get(doc_id)
        if doc is None or doc.deleted_at is not None:
            raise RegistryError("FILE_NOT_FOUND",
                                operator_detail=f"document {doc_id} not found")
        enforce("Document", action, ctx.actor,
                resource_classification=doc.classification,
                resource_workspace_id=doc.workspace_id,
                resource_owner_id=doc.uploaded_by)
        if expected_state is not None and doc.state != expected_state:
            raise RegistryError("RESOURCE_CONFLICT",
                                operator_detail=f"document is in state {doc.state}, "
                                                f"op requires {expected_state}")
        return doc

    def _require_scanned_candidate(self, doc: Document) -> None:
        outcome = self.pipeline.extractions.get(doc.id)
        if outcome is None or not outcome.scanned_candidate:
            raise RegistryError(
                "INVALID_REQUEST",
                operator_detail="OCR requires a scanned-candidate document "
                                "(run scanned_pdf_detection first)")

    def _run_page_ocr(self, ctx: Context, doc: Document) -> List[dict]:
        """Run the engine over every page, store ocr_pages rows.

        The real engine (PaddleOCR) receives the rendered page PNG. The stub engine
        receives the marker payload carrying the page's true text (its honest input
        contract — see ocr.embed_page_text); the render path is still exercised for
        real images to keep the pipeline code identical either way."""
        outcome = self.pipeline.extractions.get(doc.id)
        content = _get_content(self.pipeline, doc)
        rows: List[dict] = []
        for page in outcome.pages:
            image = pdf_mod.render_page_png(content, page.page_number)
            page_result: OcrPageResult = self.engine.recognize_page(image,
                                                                    page.page_number)
            flagged = None
            if page_result.low_confidence:
                flagged = ("mean confidence %s below threshold %s"
                           % (page_result.mean_confidence, LOW_CONFIDENCE_THRESHOLD))
            rows.append({
                "page_number": page.page_number,
                "text": page_result.text,
                "bbox_regions": [list(r.bbox) for r in page_result.regions],
                "ocr_confidence": (round(page_result.mean_confidence, 4)
                                   if page_result.mean_confidence is not None else None),
                "low_confidence": page_result.low_confidence,
                "engine": page_result.engine,
                "flagged_reason": flagged,
            })
        self.pages.replace_document(doc.id, rows)
        return rows


# -------------------------------------------------------------------------- handlers

def _plain(handler):
    return handler


def handle_page_processing(service: OcrService, ctx: Context,
                           payload: Dict[str, Any]) -> Tuple[Document, Dict[str, Any], str]:
    """Feature 04: render + recognize every page of a scanned-candidate document.
    First OCR entry point: performs the canonical EXTRACTING -> OCR transition on
    entry (owner document_ingestion per the machine — the ingestion ops deferred it
    here) — actually the machine pins EXTRACTING->OCR to document_ingestion, so the
    transition is executed by this service in that owner's name only for the routing
    decision recorded by scanned_pdf_detection."""
    doc = service._load_doc(ctx, "page_processing", payload, action="execute",
                            expected_state="EXTRACTING")
    service._require_scanned_candidate(doc)

    # Enter the OCR state (routing decision came from scanned_pdf_detection).
    sm.transition(doc.state, "OCR", owner="document_ingestion")
    enter_event = service._transition_event(ctx, "document.ocr_started", doc,
                                            result="success")
    try:
        service.store.update_state(doc.id, doc.state, "OCR", enter_event)
    except Exception as exc:
        raise RegistryError("RESOURCE_CONFLICT",
                            operator_detail=f"document {doc.id}: {exc}") from exc
    doc.state = "OCR"
    service._emit(enter_event)

    rows = service._run_page_ocr(ctx, doc)
    flagged = sum(1 for r in rows if r["low_confidence"])
    return doc, {
        "page_count": len(rows),
        "pages_ocr": [{"page_number": r["page_number"],
                       "ocr_confidence": r["ocr_confidence"],
                       "low_confidence": r["low_confidence"]} for r in rows],
        "flagged_pages": flagged,
    }, f"recognized {len(rows)} pages with engine {service.engine.name}"


def handle_region_processing(service: OcrService, ctx: Context,
                             payload: Dict[str, Any]) -> Tuple[Document, Dict[str, Any], str]:
    doc = service._load_doc(ctx, "region_processing", payload, action="execute",
                            expected_state="OCR")
    rows = service.pages.get(doc.id)
    if not rows:
        raise RegistryError("INVALID_REQUEST",
                            operator_detail="no ocr_pages yet; run page_processing")
    page_no = payload.get("page_number")
    if page_no is not None:
        if not isinstance(page_no, int) or page_no < 1:
            raise RegistryError("INVALID_REQUEST",
                                details=[{"field": "page_number",
                                          "issue": "integer >= 1"}],
                                operator_detail="page_number invalid")
        rows = [r for r in rows if r["page_number"] == page_no]
    region_count = sum(len(r["bbox_regions"]) for r in rows)
    return doc, {"regions": region_count,
                 "pages": [{"page_number": r["page_number"],
                            "regions": len(r["bbox_regions"])} for r in rows]}, (
        f"{region_count} regions across {len(rows)} page(s)")


def handle_engine_selection(service: OcrService, ctx: Context,
                            payload: Dict[str, Any]) -> Tuple[Document, Dict[str, Any], str]:
    doc = service._load_doc(ctx, "engine_selection", payload, action="execute",
                            expected_state=None)
    return doc, {"engine": service.engine.name,
                 "configurable": False,  # server-side config only (feature §28)
                 }, f"engine {service.engine.name} selected (server-side config)"


def handle_language_handling(service: OcrService, ctx: Context,
                             payload: Dict[str, Any]) -> Tuple[Document, Dict[str, Any], str]:
    doc = service._load_doc(ctx, "language_handling", payload, action="execute",
                            expected_state=None)
    lang = getattr(service.engine, "_lang", "en")
    return doc, {"language": lang, "engine": service.engine.name}, (
        f"engine language {lang}")


def handle_confidence_scores(service: OcrService, ctx: Context,
                             payload: Dict[str, Any]) -> Tuple[Document, Dict[str, Any], str]:
    doc = service._load_doc(ctx, "confidence_scores", payload, action="execute",
                            expected_state=None)
    rows = service.pages.get(doc.id)
    if not rows:
        raise RegistryError("INVALID_REQUEST",
                            operator_detail="no ocr_pages yet; run page_processing")
    return doc, {"pages": [{"page_number": r["page_number"],
                            "ocr_confidence": r["ocr_confidence"],
                            "low_confidence": r["low_confidence"],
                            "flagged_reason": r["flagged_reason"]} for r in rows],
                 "threshold": LOW_CONFIDENCE_THRESHOLD}, (
        f"confidence report for {len(rows)} pages")


def handle_text_reconstruction(service: OcrService, ctx: Context,
                               payload: Dict[str, Any]) -> Tuple[Document, Dict[str, Any], str]:
    doc = service._load_doc(ctx, "text_reconstruction", payload, action="execute",
                            expected_state="OCR")
    rows = service.pages.get(doc.id)
    if not rows:
        raise RegistryError("INVALID_REQUEST",
                            operator_detail="no ocr_pages yet; run page_processing")
    text = "\n\n".join(r["text"] for r in rows if r["text"].strip())
    return doc, {"characters": len(text), "page_count": len(rows)}, (
        f"reconstructed {len(text)} characters from {len(rows)} pages")


def handle_coordinate_mapping(service: OcrService, ctx: Context,
                              payload: Dict[str, Any]) -> Tuple[Document, Dict[str, Any], str]:
    doc = service._load_doc(ctx, "coordinate_mapping", payload, action="execute",
                            expected_state=None)
    rows = service.pages.get(doc.id)
    if not rows:
        raise RegistryError("INVALID_REQUEST",
                            operator_detail="no ocr_pages yet; run page_processing")
    total = sum(len(r["bbox_regions"]) for r in rows)
    return doc, {"mapped_regions": total,
                 "coordinate_space": "normalized 0..1000 page space"}, (
        f"{total} bboxes mapped")


def handle_ocr_failures(service: OcrService, ctx: Context,
                        payload: Dict[str, Any]) -> Tuple[Document, Dict[str, Any], str]:
    """Feature 09: read-only failure/flag report (failures/22 semantics)."""
    doc = service._load_doc(ctx, "ocr_failures", payload, action="read",
                            expected_state=None)
    rows = service.pages.get(doc.id)
    flagged = [{"page_number": r["page_number"], "reason": r["flagged_reason"]}
               for r in rows if r["low_confidence"]]
    return doc, {"flagged_pages": flagged,
                 "pages_total": len(rows),
                 "engine": service.engine.name,
                 "policy": "low-confidence pages are indexed but flagged "
                           "(failures/22_ocr_failures.md)"}, (
        f"{len(flagged)} flagged page(s)")


def handle_ocr_overview(service: OcrService, ctx: Context,
                        payload: Dict[str, Any]) -> Tuple[Document, Dict[str, Any], str]:
    doc = service._load_doc(ctx, "ocr_overview", payload, action="read",
                            expected_state=None)
    rows = service.pages.get(doc.id)
    return doc, {"pages_ocr": len(rows),
                 "engine": service.engine.name,
                 "state": doc.state}, "ocr overview"


def handle_complete_ocr(service: OcrService, ctx: Context,
                        payload: Dict[str, Any]) -> Tuple[Document, Dict[str, Any], str]:
    """The pipeline completion op (this service's own feature-04 tail, exposed for
    explicit control): OCR -> INDEXING with the canonical `document.ocr_completed`
    event — the hand-off to knowledge-fabric (build order #16)."""
    doc = service._load_doc(ctx, "complete_ocr", payload, action="execute",
                            expected_state="OCR")
    rows = service.pages.get(doc.id)
    if not rows:
        raise RegistryError("INVALID_REQUEST",
                            operator_detail="no ocr_pages yet; run page_processing")
    service._apply_transition(ctx, doc, "INDEXING",
                              canonical_event="document.ocr_completed",
                              reason=f"ocr completed: {len(rows)} pages, "
                                     f"engine {service.engine.name}")
    return doc, {"document_state": doc.state, "pages_ocr": len(rows),
                 "handoff": "INDEXING (knowledge-fabric consumes next)"}, (
        f"ocr completed; document {doc.id} -> INDEXING")


# The one internal completion used by the dispatcher's "ocr_completed" aliasing is
# handle_complete_ocr; HTTP exposes the canonical feature-file ops only.

OCR_OPS: Dict[str, Dict[str, Any]] = {
    "page_processing": {"handler": handle_page_processing, "action": "execute"},
    "region_processing": {"handler": handle_region_processing, "action": "execute"},
    "engine_selection": {"handler": handle_engine_selection, "action": "execute"},
    "language_handling": {"handler": handle_language_handling, "action": "execute"},
    "confidence_scores": {"handler": handle_confidence_scores, "action": "execute"},
    "text_reconstruction": {"handler": handle_text_reconstruction, "action": "execute"},
    "coordinate_mapping": {"handler": handle_coordinate_mapping, "action": "execute"},
    "ocr_failures": {"handler": handle_ocr_failures, "action": "read"},
    "ocr_overview": {"handler": handle_ocr_overview, "action": "read"},
    "complete_ocr": {"handler": handle_complete_ocr, "action": "execute"},
}


def execute_ocr(service: OcrService, ctx: Context, op: str,
                payload: Dict[str, Any]) -> OcrOpResult:
    """One entry point for every OCR op — exactly one `ocr.<op>` invocation audit
    event per call (success, denial, or error); OpError to the HTTP layer."""
    spec = OCR_OPS.get(op)
    if spec is None:
        raise RegistryError("INVALID_REQUEST", operator_detail=f"unknown op {op!r}")
    try:
        doc, extra, reason = spec["handler"](service, ctx, payload)
    except RegistryError as err:
        denied = err.code in DENIAL_CODES
        event = service._invocation_event(
            ctx, op, spec["action"],
            result="denied" if denied else "error",
            error_code=err.code,
            reason=err.operator_detail or getattr(err, "user_message", ""))
        service._emit(event)
        raise OpError(err, ctx.correlation_id, event["event_id"]) from err
    except Exception as err:  # engine/infra crash: still exactly-one audit event,
        # mapped to a registry code (failures/22: a down/crashed engine is
        # DEPENDENCY_UNAVAILABLE) — never a bare traceback to the caller.
        event = service._invocation_event(
            ctx, op, spec["action"], result="error",
            error_code="DEPENDENCY_UNAVAILABLE",
            reason=f"unhandled exception in op: {err}")
        service._emit(event)
        mapped = RegistryError("DEPENDENCY_UNAVAILABLE",
                               operator_detail=f"ocr engine failure: {err}")
        raise OpError(mapped, ctx.correlation_id, event["event_id"]) from err
    event = service._invocation_event(ctx, op, spec["action"], result="success",
                                      doc=doc, reason=reason)
    service._emit(event)
    service.store.append_audit(doc.id, event)
    from .ops import _now_iso
    return OcrOpResult(status="ok", resource_id=doc.id, state=doc.state,
                       audit_event_id=event["event_id"],
                       timestamp=_now_iso(), data=extra)
