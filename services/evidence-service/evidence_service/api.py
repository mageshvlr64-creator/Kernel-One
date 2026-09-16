"""Thin HTTP wrapper around the ops layer (stdlib http.server, DEC-023).

Routes (feature docs §11):
- POST /api/v1/evidence-and-provenance/<op>      -> op invocation (10 slugs from
                                                    features/14 files 01-10)
- GET  /api/v1/evidence-and-provenance/<op>/{id} -> read current record (id =
                                                    evidence_id or task_id)
- GET  /healthz                                  -> liveness (unauthenticated)

Envelope (schemas/02, api/26): success {"data": ...}; errors
{"error": {code, message, details, correlation_id}} with registry-verbatim messages.
"""
from __future__ import annotations

import json
import re
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional, Tuple

from .errors import REGISTRY, RegistryError
from .ops import OPS, EvidenceService
from .policy import Actor


def resolve_actor(authorization: Optional[str], service: EvidenceService) -> Actor:
    """Dev token auth (DEC-023): `Authorization: Bearer <dev token>`; deny-by-default."""
    if not authorization or not authorization.startswith("Bearer "):
        raise RegistryError("AUTH_REQUIRED")
    token = authorization[len("Bearer "):].strip()
    role = service.settings.dev_actor_tokens.get(token)
    if role is None:
        raise RegistryError("AUTH_REQUIRED")
    clearance = "RESTRICTED" if role == "Restricted User" else "INTERNAL"
    return Actor(actor_id=f"dev:{role.lower().replace(' ', '-')}", role=role,
                 clearance=clearance, workspace_id="ws-dev")


def _error_body(err: RegistryError, correlation_id: str) -> Dict[str, Any]:
    entry = REGISTRY[err.code]
    return {"error": {"code": err.code, "message": entry.user_message,
                      "details": err.details, "correlation_id": correlation_id}}


class Api:
    """Route table + handler dispatch shared by the HTTP wrapper and tests."""

    def __init__(self, service: EvidenceService) -> None:
        self.service = service

    def handle_invoke(self, actor: Actor, op: str, payload: Optional[dict],
                      source_ip: Optional[str] = None) -> Tuple[int, Dict[str, Any]]:
        try:
            result = self.service.invoke(op, actor, payload, source_ip=source_ip)
        except RegistryError as err:
            return err.http_status, _error_body(err, str(uuid.uuid4()))
        body = {"data": {"status": "ok", "op": result.op,
                         "resource_id": result.resource_id,
                         "state": result.state,
                         "audit_event_id": result.audit_event_id,
                         "correlation_id": result.correlation_id,
                         "timestamp": self.service.invocations[result.audit_event_id]["timestamp"],
                         "result": result.data}}
        return 200, body

    def handle_read(self, actor: Actor, op: str, record_id: str,
                    source_ip: Optional[str] = None) -> Tuple[int, Dict[str, Any]]:
        try:
            result = self.service.invoke(op, actor, _read_payload(op, record_id),
                                         source_ip=source_ip)
        except RegistryError as err:
            return err.http_status, _error_body(err, str(uuid.uuid4()))
        return 200, {"data": {"status": "ok", "op": result.op,
                              "resource_id": result.resource_id,
                              "audit_event_id": result.audit_event_id,
                              "result": result.data}}


def _read_payload(op: str, record_id: str) -> Dict[str, Any]:
    """Read paths (§11 GET): evidence-scoped ops take evidence_id; task-scoped ops
    (claim_extraction, evidence_graph, confidence, unsupported_claim_detection)
    take task_id; claim_to_source_mapping's read is claim_id-scoped."""
    task_ops = {"claim_extraction", "evidence_graph", "confidence",
                "unsupported_claim_detection"}
    claim_ops = {"claim_to_source_mapping"}
    if op in task_ops:
        return {"task_id": record_id}
    if op in claim_ops:
        return {"claim_id": record_id}
    return {"evidence_id": record_id}


def make_handler(api: Api) -> type:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # silence default stderr access log
            return

        def _deny(self, err: RegistryError) -> None:
            correlation = str(uuid.uuid4())
            self._send(err.http_status, _error_body(err, correlation))

        def _send(self, status: int, body: Dict[str, Any]) -> None:
            payload = json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def _body(self) -> Dict[str, Any]:
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b""
            if not raw:
                return {}
            try:
                parsed = json.loads(raw.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                raise RegistryError("INVALID_REQUEST",
                                    operator_detail="body is not valid JSON")
            if not isinstance(parsed, dict):
                raise RegistryError("INVALID_REQUEST",
                                    operator_detail="body must be a JSON object")
            return parsed

        def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
            # Liveness is deliberately unauthenticated (open probe) — before auth.
            if self.path.split("?", 1)[0] == "/healthz":
                self._send(200, {"data": {"status": "ok", "service": "evidence-service"}})
                return
            try:
                actor = resolve_actor(self.headers.get("Authorization"), api.service)
            except RegistryError as err:
                self._deny(err)
                return
            route = self.path.split("?", 1)[0]
            m = re.match(r"^/api/v1/evidence-and-provenance/([a-z_]+)/([^/]+)$", route)
            if m:
                op, record_id = m.group(1), m.group(2)
                if op not in OPS:
                    self._deny(RegistryError("INVALID_REQUEST",
                                             operator_detail=f"unknown op {op!r}"))
                    return
                status, body = api.handle_read(actor, op, record_id,
                                               source_ip=self.client_address[0])
                self._send(status, body)
                return
            self._deny(RegistryError("FILE_NOT_FOUND",
                                     operator_detail=f"no route {route}"))

        def do_POST(self) -> None:  # noqa: N802
            route = self.path.split("?", 1)[0]
            m = re.match(r"^/api/v1/evidence-and-provenance/([a-z_]+)$", route)
            if not m:
                self._deny(RegistryError("FILE_NOT_FOUND",
                                         operator_detail=f"no route {route}"))
                return
            try:
                actor = resolve_actor(self.headers.get("Authorization"), api.service)
                payload = self._body()
            except RegistryError as err:
                self._deny(err)
                return
            op = m.group(1)
            if op not in OPS:
                self._deny(RegistryError("INVALID_REQUEST",
                                         operator_detail=f"unknown op {op!r}"))
                return
            status, body = api.handle_invoke(actor, op, payload,
                                             source_ip=self.client_address[0])
            self._send(status, body)

    return Handler


def serve(api: Api, host: str, port: int) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), make_handler(api))
