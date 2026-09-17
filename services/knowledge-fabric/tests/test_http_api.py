from __future__ import annotations

import json
import socket
import time
import urllib.parse
import threading
import urllib.error
import urllib.request

import pytest

from knowledge_fabric.api import Api, serve
from tests.conftest import make_actor, make_document


@pytest.fixture(scope="module")
def server_url():
    from knowledge_fabric.config import Settings
    from knowledge_fabric.ops import KnowledgeFabricService
    from knowledge_fabric.storage import ChunkIndex, DocumentSource
    from knowledge_fabric.audit import InMemoryAuditSink

    svc = KnowledgeFabricService(source=DocumentSource(),
                                 index=ChunkIndex(),
                                 audit_sink=InMemoryAuditSink(),
                                 settings=Settings())
    ref = make_document(svc)
    for op in ("chunking", "embeddings", "vector_index"):
        svc.invoke(op, make_actor("Analyst"), {"document_id": ref.document_id})
    api = Api(svc)
    srv = serve(api, "127.0.0.1", 0)
    port = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{port}", ref.document_id
    srv.shutdown()


def request(method, url, token=None, body=None):
    r = urllib.request.Request(url, method=method)
    if token:
        r.add_header("Authorization", "Bearer " + token)
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, data=data) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read()
        return e.code, json.loads(raw) if raw else {}


def request_json(method, url, body, token=None):
    return request(method, url, token=token, body=body)


ADMIN = "dev-token-administrator"
ANALYST = "dev-token-analyst"


class TestHttpApi:
    def test_healthz_open(self, server_url):
        url, _ = server_url
        s, b = request("GET", url + "/healthz")
        assert s == 200 and b["data"]["service"] == "knowledge-fabric"

    def test_invoke_requires_auth(self, server_url):
        url, _ = server_url
        s, b = request_json("POST", url + "/api/v1/knowledge-fabric/hybrid_search",
                            {"query": "x"})
        assert s == 401 and b["error"]["code"] == "AUTH_REQUIRED"

    def test_invoke_success_envelope(self, server_url):
        url, doc_id = server_url
        s, b = request("POST", url + "/api/v1/knowledge-fabric/knowledge_overview",
                       ANALYST, {})
        assert s == 200
        assert b["data"]["status"] == "ok"
        assert b["data"]["audit_event_id"]
        assert b["data"]["result"]["documents_indexed"] >= 1

    def test_error_envelope_registry_message(self, server_url):
        url, _ = server_url
        s, b = request_json("POST", url + "/api/v1/knowledge-fabric/hybrid_search",
                            {}, ANALYST)
        assert s == 400
        err = b["error"]
        assert err["code"] == "INVALID_REQUEST"
        assert err["message"] == ("Your request couldn't be processed — "
                                  "check the highlighted fields.")
        assert err["correlation_id"]

    def test_unknown_op_400(self, server_url):
        url, _ = server_url
        s, b = request_json("POST", url + "/api/v1/knowledge-fabric/nonsense", {}, ANALYST)
        assert s == 400 and b["error"]["code"] == "INVALID_REQUEST"

    def test_read_route(self, server_url):
        url, doc_id = server_url
        s, b = request("GET", f"{url}/api/v1/knowledge-fabric/knowledge_overview/{doc_id}",
                       ANALYST)
        assert s == 200 and b["data"]["resource_id"] == doc_id

    def test_search_over_http(self, server_url):
        url, _ = server_url
        s, b = request("POST", url + "/api/v1/knowledge-fabric/hybrid_search",
                       ANALYST, {"query": "pump alignment"})
        assert s == 200
        assert "hits" in b["data"]["result"]

    def test_denied_role_is_tool_not_allowed(self, server_url):
        url, doc_id = server_url
        s, b = request_json("POST", url + "/api/v1/knowledge-fabric/chunking",
                            {"document_id": doc_id}, "dev-token-auditor")
        assert s == 403 and b["error"]["code"] == "TOOL_NOT_ALLOWED"


class TestDeniedPostDrainsBody:
    """Regression: a denied POST must not close the connection while the client
    is still sending its body. POST handlers authenticate before draining the
    body, so a denial was written and the socket closed with unread body bytes
    pending - a client mid-body then hit an aborted connection (WinError 10053
    on Windows), a load-dependent flake. The raw-socket client below sends
    headers plus half the body, pauses, then finishes: with the drain in place
    the server waits for the rest and the denial arrives cleanly."""

    PATH = "/api/v1/knowledge-fabric/hybrid_search"
    BODY = {"query": "pump alignment"}

    def test_denied_post_mid_body_still_gets_clean_response(self, server_url):
        url, _ = server_url
        base = url
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
