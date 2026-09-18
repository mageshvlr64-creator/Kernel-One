"""Thin HTTP wrapper around the ops layer (stdlib http.server, DEC-023).

Routes (feature docs §11):
- POST /api/v1/knowledge-fabric/<op>      -> op invocation (15 slugs from features/13)
- GET  /api/v1/knowledge-fabric/<op>/{id} -> read current index record for a document
                                             (§11 read path; id = document_id)
- GET  /healthz                           -> liveness (unauthenticated open probe)

Envelope (schemas/02, api/26): success {"data": ...}; errors
{"error": {code, message, details, correlation_id}} with registry-verbatim messages.
"""
from __future__ import annotations

import json
import re
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import IO, Any, Dict, Optional, Tuple

from .errors import REGISTRY, RegistryError
from .ops import OPS, KnowledgeFabricService
from .policy import Actor


def resolve_actor(authorization: Optional[str], service: KnowledgeFabricService) -> Actor:
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

    def __init__(self, service: KnowledgeFabricService) -> None:
        self.service = service

    def handle_invoke(self, actor: Actor, op: str, payload: Optional[dict],
                      source_ip: Optional[str] = None) -> Tuple[int, Dict[str, Any]]:
        try:
            result = self.service.invoke(op, actor, payload, source_ip=source_ip)
        except RegistryError as err:
            return err.http_status, _error_body(err, str(uuid.uuid4()))
        body = {"data": {"status": "ok", "op": result.op, "resource_id": result.resource_id,
                         "state": result.state, "audit_event_id": result.audit_event_id,
                         "correlation_id": result.correlation_id,
                         "timestamp": self.service.invocations[result.audit_event_id]["timestamp"],
                         "result": result.data}}
        return 200, body

    def handle_read(self, actor: Actor, op: str, document_id: str,
                    source_ip: Optional[str] = None) -> Tuple[int, Dict[str, Any]]:
        try:
            result = self.service.invoke(op, actor, {"document_id": document_id},
                                         source_ip=source_ip)
        except RegistryError as err:
            return err.http_status, _error_body(err, str(uuid.uuid4()))
        return 200, {"data": {"status": "ok", "op": result.op,
                              "resource_id": result.resource_id,
                              "audit_event_id": result.audit_event_id,
                              "result": result.data}}


def make_handler(api: Api) -> type:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # silence default stderr access log
            return

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
            self._body_consumed = length
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
                self._send(200, {"data": {"status": "ok", "service": "knowledge-fabric"}})
                return
            try:
                actor = resolve_actor(self.headers.get("Authorization"), api.service)
            except RegistryError as err:
                self._deny(err)
                return
            route = self.path.split("?", 1)[0]
            m = re.match(r"^/api/v1/knowledge-fabric/([a-z_]+)/([^/]+)$", route)
            if m:
                op, document_id = m.group(1), m.group(2)
                if op not in OPS:
                    self._deny(RegistryError("INVALID_REQUEST",
                                             operator_detail=f"unknown op {op!r}"))
                    return
                status, body = api.handle_read(actor, op, document_id,
                                               source_ip=self.client_address[0])
                self._send(status, body)
                return
            self._deny(RegistryError("FILE_NOT_FOUND",
                                     operator_detail=f"no route {route}"))

        def do_POST(self) -> None:  # noqa: N802
            route = self.path.split("?", 1)[0]
            m = re.match(r"^/api/v1/knowledge-fabric/([a-z_]+)$", route)
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
