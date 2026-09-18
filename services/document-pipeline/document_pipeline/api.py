"""Thin HTTP wrapper around the ops layer.

Routes (per docs/api/11_documents_api.md + feature docs §11):
- POST /api/v1/documents                -> upload_validation (REST create path)
- GET  /api/v1/documents/{id}           -> read the Document (api/11 row 2)
- GET  /api/v1/documents                -> paginated list (api/11 row 3)
- POST /api/v1/document-ingestion/{op}  -> the seven feature-op routes (§11), where
                                           op is the kebab-case feature-file slug
- GET  /healthz                         -> liveness (api/24 shape, minimal)

Envelope rules (docs/schemas/02_api_schema.md, docs/api/26_error_contracts.md):
- success: {"data": ...}; errors: {"error": {code, message, details, correlation_id}}
- code always from the canonical registry; message always the registry's user message;
  details only for INVALID_REQUEST; HTTP status always the registry's status.

Auth: dev bearer-token stub per DEC-023 (see policy.py) — identity-service (Character 5)
replaces it. actor_id/workspace_id are taken from the server-side actor record, never from
client-supplied body fields (feature §6). Rate limiting (429 RATE_LIMITED) and the full
pagination contract are API-gateway concerns that land with services/api (Character 1);
this wrapper honors limit/cursor defaults for the list route only.
"""
from __future__ import annotations

import json
import re
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import IO, Any, Dict, Optional, Tuple

from .domain import Document
from .errors import RegistryError
from .ops import Context, DocumentIngestionService, OpError, execute
from .policy import Actor, DEV_ACTOR_TOKENS

MAX_BODY_BYTES = 300 * 1024 * 1024  # 200MB upload -> ~267MB base64; hard request cap

# kebab-case URL slug -> snake_case op name (feature file slugs per §11)
_OP_SLUGS = {
    "ingestion-overview": "ingestion_overview",
    "upload-validation": "upload_validation",
    "file-type-detection": "file_type_detection",
    "native-pdf-parsing": "native_pdf_parsing",
    "scanned-pdf-detection": "scanned_pdf_detection",
    "page-extraction": "page_extraction",
    "metadata-extraction": "metadata_extraction",
}

# OCR feature-file slugs (features/11_ocr §11) -> ocr_ops op names, plus the service's
# explicit pipeline-completion op (OCR -> INDEXING hand-off to knowledge-fabric).
_OCR_OP_SLUGS = {
    "ocr-overview": "ocr_overview",
    "engine-selection": "engine_selection",
    "language-handling": "language_handling",
    "page-processing": "page_processing",
    "region-processing": "region_processing",
    "confidence-scores": "confidence_scores",
    "text-reconstruction": "text_reconstruction",
    "coordinate-mapping": "coordinate_mapping",
    "ocr-failures": "ocr_failures",
    "complete-ocr": "complete_ocr",
}

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)


def _document_wire(doc: Document) -> Dict[str, Any]:
    return doc.to_dict()


def resolve_actor(auth_header: Optional[str]) -> Actor:
    """Dev bearer-token auth (DEC-023). Returns the server-side actor record."""
    if not auth_header or not auth_header.startswith("Bearer "):
        raise RegistryError("AUTH_REQUIRED", operator_detail="missing bearer token")
    token = auth_header[len("Bearer "):].strip()
    actor = DEV_ACTOR_TOKENS.get(token)
    if actor is None:
        raise RegistryError("AUTH_REQUIRED", operator_detail="unknown or expired token")
    return actor


class Api:
    """Framework-agnostic request handlers; the HTTP server below is a thin adapter."""

    def __init__(self, service: DocumentIngestionService) -> None:
        self.service = service
        from .ocr_ops import OcrService
        self.ocr = OcrService(service)  # feature group 11 shares this service

    # ---- POST /api/v1/ocr/{op} (features/11_ocr §11) ----

    def handle_ocr_op(self, actor: Actor, op_slug: str, body: Dict[str, Any],
                      *, session_id: Optional[str] = None,
                      source_ip: Optional[str] = None,
                      idempotency_key: Optional[str] = None) -> Tuple[int, Dict[str, Any]]:
        from .ocr_ops import execute_ocr
        op = _OCR_OP_SLUGS.get(op_slug)
        if op is None:
            err = RegistryError("INVALID_REQUEST",
                                operator_detail=f"unknown ocr operation {op_slug!r}")
            return err.http_status, _error_body(err, str(uuid.uuid4()))
        ctx = Context(actor=actor, session_id=session_id,
                      source_ip=source_ip, idempotency_key=idempotency_key)
        try:
            result = execute_ocr(self.ocr, ctx, op, body)
        except OpError as op_err:
            return op_err.err.http_status, {
                "error": {
                    "code": op_err.err.code,
                    "message": op_err.err.user_message,
                    "details": {"field_errors": op_err.err.details}
                    if op_err.err.details else None,
                    "correlation_id": op_err.correlation_id,
                }
            }
        except RegistryError as err:
            return err.http_status, _error_body(err, ctx.correlation_id)
        data = {
            "status": result.status,
            "resource_id": result.resource_id,
            "state": result.state,
            "audit_event_id": result.audit_event_id,
            "timestamp": result.timestamp,
            **({"data": result.data} if result.data else {}),
        }
        return 200, {"data": data}

    # ---- POST /api/v1/document-ingestion/{op} ----

    def handle_op(self, actor: Actor, op_slug: str, body: Dict[str, Any],
                  *, session_id: Optional[str] = None, source_ip: Optional[str] = None,
                  idempotency_key: Optional[str] = None) -> Tuple[int, Dict[str, Any]]:
        op = _OP_SLUGS.get(op_slug)
        if op is None:
            err = RegistryError("INVALID_REQUEST",
                                operator_detail=f"unknown operation {op_slug!r}")
            return err.http_status, _error_body(err, str(uuid.uuid4()))
        ctx = Context(actor=actor, session_id=session_id,
                      source_ip=source_ip, idempotency_key=idempotency_key)
        try:
            result = execute(self.service, ctx, op, body)
        except OpError as op_err:
            return op_err.err.http_status, {
                "error": {
                    "code": op_err.err.code,
                    "message": op_err.err.user_message,
                    "details": {"field_errors": op_err.err.details}
                    if op_err.err.details else None,
                    "correlation_id": op_err.correlation_id,
                }
            }
        except RegistryError as err:
            # e.g. the audit sink itself failed while emitting the invocation event —
            # fail with a registry-shaped response rather than an unhandled traceback.
            return err.http_status, _error_body(err, ctx.correlation_id)
        data = {
            "status": result.status,
            "resource_id": result.resource_id,
            "state": result.state,
            "audit_event_id": result.audit_event_id,
            "timestamp": result.timestamp,
            **({"data": result.data} if result.data else {}),
        }
        return 200, {"data": data}

    # ---- DELETE /api/v1/documents/{id} (api/11 row 4: soft-delete, ownership or admin) ----

    def handle_delete_document(self, actor: Actor, doc_id: str,
                               source_ip: Optional[str] = None) -> Tuple[int, Dict[str, Any]]:
        from . import statemachine as sm
        from .policy import check
        if not _UUID_RE.match(doc_id or ""):
            err = RegistryError("INVALID_REQUEST", details=[{
                "field": "id", "message": "must be a uuid"}])
            return err.http_status, _error_body(err, str(uuid.uuid4()))
        doc = self.service.store.get(doc_id)
        if doc is None or doc.deleted_at is not None:
            err = RegistryError("FILE_NOT_FOUND",
                                operator_detail=f"document {doc_id} not found",
                                resource_id=doc_id)
            return err.http_status, _error_body(err, str(uuid.uuid4()))
        ctx = Context(actor=actor, source_ip=source_ip)
        decision = check("Document", "delete", actor,
                         resource_classification=doc.classification,
                         resource_workspace_id=doc.workspace_id,
                         resource_owner_id=doc.uploaded_by)
        if not decision.allowed:
            err = RegistryError(decision.code, operator_detail=decision.rule,
                                resource_id=doc.id)
            event = self.service._invocation_event(
                ctx, "delete_document", "delete", result="denied", doc=doc,
                error_code=decision.code, reason=decision.rule, decision="denied")
            self.service._emit(event)
            return err.http_status, _error_body(err, ctx.correlation_id)
        # Canonical machine: DELETED is entered from READY only.
        if doc.state != "READY":
            err = RegistryError("RESOURCE_CONFLICT",
                                operator_detail=f"document is in state {doc.state}; "
                                                f"delete requires READY")
            return err.http_status, _error_body(err, ctx.correlation_id)
        sm.transition("READY", "DELETED", owner="document_ingestion")
        event = self.service._transition_event(ctx, "document.deleted", doc,
                                               result="success")
        self.service.store.soft_delete(doc.id, event)
        self.service._emit(event)
        return 204, {}

    # ---- POST /api/v1/documents (api/11 row 1) ----

    def handle_create_document(self, actor: Actor, body: Dict[str, Any], **kwargs) -> Tuple[int, Dict[str, Any]]:
        return self.handle_op(actor, "upload-validation", body, **kwargs)

    # ---- GET /api/v1/documents/{id} (api/11 row 2) ----

    def handle_get_document(self, actor: Actor, doc_id: str,
                            source_ip: Optional[str] = None) -> Tuple[int, Dict[str, Any]]:
        if not _UUID_RE.match(doc_id or ""):
            err = RegistryError("INVALID_REQUEST", details=[{
                "field": "id", "message": "must be a uuid"}])
            return err.http_status, _error_body(err, actor.actor_id)
        doc = self.service.store.get(doc_id)
        if doc is None or doc.deleted_at is not None:
            err = RegistryError("FILE_NOT_FOUND",
                                operator_detail=f"document {doc_id} not found",
                                resource_id=doc_id)
            return err.http_status, _error_body(err, str(uuid.uuid4()))
        # Read permission with FILE_NOT_FOUND-compatible behavior: api/11 row 2 says
        # below-clearance reads get FILE_CLASSIFICATION_DENIED; role denies are
        # POLICY_DENIED/TOOL_NOT_ALLOWED. Denied reads are audited (feature §16).
        from .policy import check
        decision = check("Document", "read", actor,
                         resource_classification=doc.classification,
                         resource_workspace_id=doc.workspace_id,
                         resource_owner_id=doc.uploaded_by)
        if not decision.allowed:
            err = RegistryError(decision.code, operator_detail=decision.rule,
                                resource_id=doc.id)
            ctx = Context(actor=actor, source_ip=source_ip)
            event = self.service._invocation_event(
                ctx, "read_document", "read",
                result="denied", doc=doc, error_code=decision.code,
                reason=decision.rule, decision="denied",
            )
            self.service._emit(event)
            return err.http_status, _error_body(err, ctx.correlation_id)
        # Allowed read: one audited event (canonical read audit, api/11 row 2). Event type
        # uses the document.* namespace; this REST read is not one of the seven feature ops.
        ctx = Context(actor=actor, source_ip=source_ip)
        event = self.service._invocation_event(
            ctx, "read_document", "read", result="success", doc=doc, decision="allowed",
        )
        self.service._emit(event)
        return 200, {"data": _document_wire(doc)}

    # ---- GET /api/v1/documents (api/11 row 3) ----

    def handle_list_documents(self, actor: Actor, workspace_id: Optional[str],
                              state: Optional[str], cursor: Optional[str],
                              limit_raw: Optional[str],
                              source_ip: Optional[str] = None) -> Tuple[int, Dict[str, Any]]:
        from .policy import check, CLEARANCE_ORDER
        ws = workspace_id or actor.workspace_id
        if actor.role not in ("Administrator", "Auditor") and ws != actor.workspace_id:
            err = RegistryError("POLICY_DENIED",
                                operator_detail="list scoped to caller's workspace")
            return err.http_status, _error_body(err, actor.actor_id)

        try:
            limit = int(limit_raw) if limit_raw is not None else 50
        except ValueError:
            limit = 50
        limit = max(1, min(limit, 200))  # schemas/02: default 50, max 200

        docs = [d for d in self.service.store.list_by_workspace(ws)]
        # Classification filter per caller clearance (api/11 row 3).
        clearance = CLEARANCE_ORDER[actor.clearance]
        docs = [d for d in docs if CLEARANCE_ORDER[d.classification] <= clearance]
        if state:
            docs = [d for d in docs if d.state == state]
        # Cursor = last id in the previous page (stable given append-only ids).
        if cursor:
            idx = next((i for i, d in enumerate(docs) if d.id == cursor), None)
            if idx is not None:
                docs = docs[idx + 1:]
        page = docs[:limit]
        next_cursor = page[-1].id if len(docs) > limit else None
        event = self.service._invocation_event(
            Context(actor=actor, source_ip=source_ip),
            "list_documents", "read", result="success", decision="allowed",
        )
        self.service._emit(event)
        body: Dict[str, Any] = {"data": [_document_wire(d) for d in page]}
        if next_cursor:
            body["pagination"] = {"next_cursor": next_cursor, "limit": limit}
        return 200, body


def _error_body(err: RegistryError, correlation_id: str) -> Dict[str, Any]:
    return {
        "error": {
            "code": err.code,
            "message": err.user_message,
            "details": {"field_errors": err.details} if err.details else None,
            "correlation_id": correlation_id or str(uuid.uuid4()),
        }
    }


def make_handler(api: Api):
    """Build a BaseHTTPRequestHandler bound to this Api."""

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt, *args):  # quiet default logging; ops layer logs
            pass

        def _headers_common(self) -> Dict[str, str]:
            return {"Content-Type": "application/json; charset=utf-8"}

        def _read_json(self) -> Dict[str, Any]:
            length = int(self.headers.get("Content-Length") or 0)
            self._body_consumed = length
            if length <= 0:
                return {}
            if length > MAX_BODY_BYTES:
                raise RegistryError("INVALID_REQUEST",
                                    operator_detail="request body too large")
            raw = self.rfile.read(length)
            try:
                parsed = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise RegistryError("INVALID_REQUEST",
                                    operator_detail=f"body is not valid JSON: {exc}") from exc
            if not isinstance(parsed, dict):
                raise RegistryError("INVALID_REQUEST",
                                    operator_detail="body must be a JSON object")
            return parsed

        def _send(self, status: int, body: Dict[str, Any]) -> None:
            payload = json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def _send_no_content(self) -> None:
            self.send_response(204)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def _drain_unread_body(self) -> None:
            """Consume an unread request body before writing a denial response.

            POST handlers authenticate before reading the body, so a denial
            (401/403/400) would otherwise be written while the client is still
            sending body bytes. Closing with unread input makes Windows abort
            the connection (WinError 10053 / ConnectionAbortedError) instead of
            delivering the error — a load-dependent flake. Only bytes not
            already consumed by the body reader are drained.
            """
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = 0
            remaining = length - getattr(self, "_body_consumed", 0)
            stream: IO[bytes] = self.rfile
            while remaining > 0:
                block = stream.read(min(remaining, 65536))
                if not block:
                    # Peer hung up before the whole body arrived; stop draining.
                    break
                remaining -= len(block)

        def _deny(self, err: RegistryError) -> None:
            self._drain_unread_body()
            # AUTH_REQUIRED is an audited code (registry); actor_id='system' is the schema's
            # provision for events without an authenticated actor.
            correlation = str(uuid.uuid4())
            if err.code == "AUTH_REQUIRED":
                from .audit import build_audit_event
                event = build_audit_event(
                    event_type="document.auth_required",
                    actor_id="system", action="read", resource_type="Document",
                    result="error", error_code=err.code,
                    reason=err.operator_detail, correlation_id=correlation,
                )
                api.service._emit(event)
            self._send(err.http_status, _error_body(err, correlation))

        def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
            # Liveness is deliberately unauthenticated (open probe) — check it before auth.
            route0 = self.path.split("?", 1)[0]
            if route0 == "/healthz":
                self._send(200, {"data": {"status": "ok", "service": "document-pipeline"}})
                return
            try:
                actor = resolve_actor(self.headers.get("Authorization"))
            except RegistryError as err:
                self._deny(err)
                return
            path = self.path.split("?", 1)
            route, query = path[0], path[1] if len(path) > 1 else ""
            params = dict(p.split("=", 1) for p in query.split("&") if "=" in p)
            if route == "/api/v1/documents" :
                status, body = api.handle_list_documents(
                    actor, params.get("workspace_id"), params.get("state"),
                    params.get("cursor"), params.get("limit"),
                    source_ip=self.client_address[0])
                self._send(status, body)
                return
            m = re.match(r"^/api/v1/documents/([^/]+)$", route)
            if m:
                status, body = api.handle_get_document(
                    actor, m.group(1), source_ip=self.client_address[0])
                self._send(status, body)
                return
            self._deny(RegistryError("FILE_NOT_FOUND",
                                     operator_detail=f"no route {route}"))

        def do_DELETE(self) -> None:  # noqa: N802
            try:
                actor = resolve_actor(self.headers.get("Authorization"))
            except RegistryError as err:
                self._deny(err)
                return
            route = self.path.split("?", 1)[0]
            m = re.match(r"^/api/v1/documents/([^/]+)$", route)
            if m:
                status, body = api.handle_delete_document(
                    actor, m.group(1), source_ip=self.client_address[0])
                if status == 204:
                    self._send_no_content()
                else:
                    self._send(status, body)
                return
            self._deny(RegistryError("FILE_NOT_FOUND",
                                     operator_detail=f"no route {route}"))

        def do_POST(self) -> None:  # noqa: N802
            try:
                actor = resolve_actor(self.headers.get("Authorization"))
            except RegistryError as err:
                self._deny(err)
                return
            route = self.path.split("?", 1)[0]
            try:
                body = self._read_json()
            except RegistryError as err:
                self._deny(err)
                return
            if route == "/api/v1/documents":
                status, resp = api.handle_create_document(
                    actor, body, session_id=None,
                    source_ip=self.client_address[0],
                    idempotency_key=self.headers.get("Idempotency-Key"))
                self._send(status, resp)
                return
            m = re.match(r"^/api/v1/document-ingestion/([a-z0-9\-]+)$", route)
            if m:
                status, resp = api.handle_op(
                    actor, m.group(1), body, session_id=None,
                    source_ip=self.client_address[0],
                    idempotency_key=self.headers.get("Idempotency-Key"))
                self._send(status, resp)
                return
            m = re.match(r"^/api/v1/ocr/([a-z0-9\-]+)$", route)
            if m:
                status, resp = api.handle_ocr_op(
                    actor, m.group(1), body, session_id=None,
                    source_ip=self.client_address[0],
                    idempotency_key=self.headers.get("Idempotency-Key"))
                self._send(status, resp)
                return
            self._deny(RegistryError("FILE_NOT_FOUND",
                                     operator_detail=f"no route {route}"))

    return Handler


def serve(api: Api, host: str, port: int) -> ThreadingHTTPServer:
    handler = make_handler(api)
    server = ThreadingHTTPServer((host, port), handler)
    return server
