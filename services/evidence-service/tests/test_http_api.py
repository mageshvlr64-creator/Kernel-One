from __future__ import annotations

import json
import socket
import time
import urllib.parse
import threading
import urllib.error
import urllib.request

import pytest

from evidence_service.api import Api, serve
from evidence_service.audit import InMemoryAuditSink
from evidence_service.claims import ClaimStore
from evidence_service.config import Settings
from evidence_service.ops import EvidenceService
from evidence_service.storage import EvidenceLinks, RetrievalView, SourceChainStore
from tests.conftest import (CHUNK_ID, DOC_ID, TASK_ID, evidence_payload,
                            make_actor, seed_chain, seed_chunk)


def evidence_payload_http(**overrides) -> dict:
    payload = evidence_payload(**overrides)
    payload["source_hash"] = "a" * 64  # must match the seeded chain row's sha256
    return payload


@pytest.fixture()
def http_server():
    service = EvidenceService(links=EvidenceLinks(), claims_store=ClaimStore(),
                              chains=SourceChainStore(), retrieval=RetrievalView(),
                              audit_sink=InMemoryAuditSink(), settings=Settings())
    seed_chain(service, version=1)
    seed_chunk(service, chunk_id=CHUNK_ID, document_id=DOC_ID, page_number=3)
    api = Api(service)
    server = serve(api, "127.0.0.1", 0)
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{port}", service
    server.shutdown()
    server.server_close()


def _post(base, path, payload, token="dev-token-analyst"):
    req = urllib.request.Request(
        base + path, data=json.dumps(payload).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read().decode("utf-8"))


def _get(base, path, token="dev-token-analyst"):
    req = urllib.request.Request(base + path, method="GET",
                                 headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read().decode("utf-8"))


class TestHttpApi:
    def test_healthz_open(self, http_server):
        base, _ = http_server
        status, body = _get(base, "/healthz", token=None)
        assert status == 200
        assert body["data"]["service"] == "evidence-service"

    def test_unauthenticated_401(self, http_server):
        base, _ = http_server
        status, body = _post(base, "/api/v1/evidence-and-provenance/evidence_system",
                             evidence_payload(), token=None)
        assert status == 401
        assert body["error"]["code"] == "AUTH_REQUIRED"

    def test_bad_token_401(self, http_server):
        base, _ = http_server
        status, body = _post(base, "/api/v1/evidence-and-provenance/evidence_system",
                             evidence_payload(), token="dev-token-nobody")
        assert status == 401

    def test_create_and_read_roundtrip(self, http_server):
        base, _ = http_server
        status, body = _post(base, "/api/v1/evidence-and-provenance/evidence_system",
                             evidence_payload_http())
        assert status == 200
        data = body["data"]
        assert data["status"] == "ok"
        assert data["op"] == "evidence_system"
        eid = data["result"]["evidence"]["id"]
        assert data["audit_event_id"]
        status, body = _get(base, f"/api/v1/evidence-and-provenance/source_chain/{eid}")
        assert status == 200
        assert body["data"]["result"]["chain"][0]["version"] == 1

    def test_denied_role_403_envelope(self, http_server):
        base, _ = http_server
        status, body = _post(base, "/api/v1/evidence-and-provenance/evidence_system",
                             evidence_payload(), token="dev-token-auditor")
        assert status == 403
        assert body["error"]["code"] == "TOOL_NOT_ALLOWED"
        assert body["error"]["correlation_id"]

    def test_unknown_op_400(self, http_server):
        base, _ = http_server
        status, body = _post(base, "/api/v1/evidence-and-provenance/not_an_op", {})
        assert status == 400
        assert body["error"]["code"] == "INVALID_REQUEST"

    def test_unknown_route_404(self, http_server):
        base, _ = http_server
        status, body = _get(base, "/api/v1/nothing-here")
        assert status == 404
        assert body["error"]["code"] == "FILE_NOT_FOUND"

    def test_malformed_json_400(self, http_server):
        base, _ = http_server
        req = urllib.request.Request(
            base + "/api/v1/evidence-and-provenance/evidence_system",
            data=b"{not json", method="POST",
            headers={"Content-Type": "application/json",
                     "Authorization": "Bearer dev-token-analyst"})
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                status = resp.status
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            status = err.code
            body = json.loads(err.read().decode("utf-8"))
        assert status == 400
        assert body["error"]["code"] == "INVALID_REQUEST"

    def test_error_envelope_registry_verbatim(self, http_server):
        base, _ = http_server
        status, body = _post(base, "/api/v1/evidence-and-provenance/claim_extraction", {})
        assert status == 400
        assert body["error"]["message"] == (
            "Your request couldn't be processed — check the highlighted fields.")

    def test_http_audit_invariant(self, http_server):
        base, service = http_server
        before = len(service.audit_sink.events)
        _post(base, "/api/v1/evidence-and-provenance/evidence_system", evidence_payload_http())
        _post(base, "/api/v1/evidence-and-provenance/evidence_system",
              evidence_payload_http(), token="dev-token-auditor")
        events = service.audit_sink.events[before:]
        assert len(events) == 2
        assert [e["result"] for e in events] == ["success", "error"]


class TestDeniedPostDrainsBody:
    """Regression: a denied POST must not close the connection while the client
    is still sending its body. POST handlers authenticate before draining the
    body, so a denial was written and the socket closed with unread body bytes
    pending - a client mid-body then hit an aborted connection (WinError 10053
    on Windows), a load-dependent flake. The raw-socket client below sends
    headers plus half the body, pauses, then finishes: with the drain in place
    the server waits for the rest and the denial arrives cleanly."""

    PATH = "/api/v1/evidence-and-provenance/evidence_system"
    BODY = evidence_payload_http()

    def test_denied_post_mid_body_still_gets_clean_response(self, http_server):
        base, _ = http_server
        payload = json.dumps(self.BODY).encode("utf-8")
        parsed = urllib.parse.urlsplit(base)
        crlf = bytes((13, 10))
        sock = socket.create_connection((parsed.hostname, parsed.port), timeout=10)
        try:
            head = crlf.join([
                ("POST " + self.PATH + " HTTP/1.1").encode("ascii"),
                ("Host: " + parsed.hostname + ":" + str(parsed.port)).encode("ascii"),
                ("Content-Type: application/json").encode("ascii"),
                ("Authorization: Bearer dev-token-nobody").encode("ascii"),
                ("Content-Length: " + str(len(payload))).encode("ascii"),
                ("Connection: close").encode("ascii"),
                b"",
            ])
            sock.sendall(head + payload[: len(payload) // 2])
            time.sleep(1.5)  # server decides the denial while we are mid-body
            try:
                sock.sendall(payload[len(payload) // 2:])
                sock.shutdown(socket.SHUT_WR)
            except OSError as exc:
                raise AssertionError(
                    "connection aborted while still sending the body: " + repr(exc))
            response = b""
            while True:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                response += chunk
        finally:
            sock.close()
        status_line = response.split(crlf, 1)[0]
        assert b" 401 " in status_line
        assert b"AUTH_REQUIRED" in response
