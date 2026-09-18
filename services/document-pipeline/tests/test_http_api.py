"""HTTP API tests — envelope shapes (schemas/02, api/26), registry statuses, api/11 routes."""
from __future__ import annotations

import json
import socket
import time
import urllib.parse
import threading
import urllib.error
import urllib.request
from typing import Optional, Tuple

import pytest

from document_pipeline.api import Api, serve

from .conftest import b64, make_pdf


@pytest.fixture(scope="module")
def server_url():
    """One server for the module; isolated per-test by unique uploads where needed."""
    from document_pipeline.audit import InMemoryAuditSink
    from document_pipeline.config import Settings
    from document_pipeline.ops import DocumentIngestionService
    from document_pipeline.store import InMemoryDocumentStore
    from document_pipeline.storage import StubObjectStorage
    import tempfile
    tmp = tempfile.mkdtemp()
    service = DocumentIngestionService(
        store=InMemoryDocumentStore(),
        storage=StubObjectStorage(tmp),
        audit_sink=InMemoryAuditSink(),
        settings=Settings(),
    )
    api = Api(service)
    httpd = serve(api, "127.0.0.1", 0)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    httpd.shutdown()


def request(method: str, url: str, token: Optional[str] = None,
            body: Optional[dict] = None) -> Tuple[int, dict]:
    req = urllib.request.Request(url, method=method)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data=data) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        return exc.code, json.loads(raw) if raw else {}


ADMIN = "dev-token-administrator"
ANALYST = "dev-token-analyst"


class TestAuth:
    def test_missing_token_is_401_auth_required(self, server_url):
        status, body = request("GET", f"{server_url}/api/v1/documents")
        assert status == 401
        assert body["error"]["code"] == "AUTH_REQUIRED"
        assert body["error"]["correlation_id"]

    def test_unknown_token_is_401(self, server_url):
        status, body = request("GET", f"{server_url}/api/v1/documents", token="nope")
        assert status == 401
        assert body["error"]["code"] == "AUTH_REQUIRED"

    def test_healthz_is_open(self, server_url):
        status, body = request("GET", f"{server_url}/healthz")
        assert status == 200
        assert body["data"]["service"] == "document-pipeline"


class TestEnvelopes:
    def test_success_uses_data_envelope(self, server_url):
        status, body = request("POST", f"{server_url}/api/v1/documents", ANALYST,
                               {"filename": "a.csv", "content_base64": b64(b"a,b\n1,2\n")})
        assert status == 200
        assert body["data"]["state"] == "UPLOADED"
        assert body["data"]["resource_id"]
        assert body["data"]["audit_event_id"]

    def test_error_envelope_shape_and_registry_message(self, server_url):
        status, body = request("POST", f"{server_url}/api/v1/documents", ANALYST, {})
        assert status == 400
        err = body["error"]
        assert err["code"] == "INVALID_REQUEST"
        assert err["message"] == ("Your request couldn't be processed — "
                                  "check the highlighted fields.")
        assert err["details"]["field_errors"]
        assert err["correlation_id"]

    def test_invalid_json_body(self, server_url):
        req = urllib.request.Request(f"{server_url}/api/v1/documents", method="POST",
                                     data=b"{not json")
        req.add_header("Authorization", f"Bearer {ANALYST}")
        try:
            with urllib.request.urlopen(req) as resp:
                status, body = resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            status, body = exc.code, json.loads(exc.read())
        assert status == 400
        assert body["error"]["code"] == "INVALID_REQUEST"


class TestDocumentsApi:
    def test_get_document_roundtrip(self, server_url):
        _, up = request("POST", f"{server_url}/api/v1/documents", ANALYST,
                        {"filename": "spec.pdf",
                         "content_base64": b64(make_pdf(pages=1))})
        doc_id = up["data"]["resource_id"]
        status, body = request("GET", f"{server_url}/api/v1/documents/{doc_id}", ANALYST)
        assert status == 200
        doc = body["data"]
        assert doc["id"] == doc_id
        assert doc["mime_type"] == "application/pdf"
        assert doc["state"] == "UPLOADED"
        assert doc["classification"] == "INTERNAL"

    def test_get_unknown_document_404(self, server_url):
        status, body = request("GET", f"{server_url}/api/v1/documents/"
                                      f"00000000-0000-0000-0000-000000000000", ANALYST)
        assert status == 404
        assert body["error"]["code"] == "FILE_NOT_FOUND"

    def test_list_is_classification_filtered(self, server_url):
        request("POST", f"{server_url}/api/v1/documents", ADMIN,
                {"filename": "secret.txt", "content_base64": b64(b"restricted contents"),
                 "classification": "RESTRICTED"})
        status, admin_list = request("GET", f"{server_url}/api/v1/documents", ADMIN)
        assert status == 200
        _, analyst_list = request("GET", f"{server_url}/api/v1/documents", ANALYST)
        admin_ids = {d["id"] for d in admin_list["data"]}
        analyst_ids = {d["id"] for d in analyst_list["data"]}
        assert analyst_ids <= admin_ids  # analyst never sees above-clearance docs

    def test_feature_op_over_http(self, server_url):
        _, up = request("POST", f"{server_url}/api/v1/documents", ANALYST,
                        {"filename": "spec.pdf",
                         "content_base64": b64(make_pdf(pages=2))})
        doc_id = up["data"]["resource_id"]
        status, body = request(
            "POST", f"{server_url}/api/v1/document-ingestion/file-type-detection",
            ANALYST, {"document_id": doc_id})
        assert status == 200
        assert body["data"]["state"] == "EXTRACTING"

    def test_unknown_feature_op_is_400(self, server_url):
        status, body = request("POST", f"{server_url}/api/v1/document-ingestion/nope",
                               ANALYST, {})
        assert status == 400
        assert body["error"]["code"] == "INVALID_REQUEST"

    def test_forbidden_op_denied_with_registry_status(self, server_url):
        _, up = request("POST", f"{server_url}/api/v1/documents", ANALYST,
                        {"filename": "a.csv", "content_base64": b64(b"a,b\n1,2\n")})
        status, body = request(
            "POST", f"{server_url}/api/v1/document-ingestion/file-type-detection",
            "dev-token-auditor", {"document_id": up["data"]["resource_id"]})
        assert status == 403
        assert body["error"]["code"] == "TOOL_NOT_ALLOWED"

    def test_delete_roundtrip_requires_ready(self, server_url):
        _, up = request("POST", f"{server_url}/api/v1/documents", ADMIN,
                        {"filename": "ready.txt", "content_base64": b64(b"hello")})
        doc_id = up["data"]["resource_id"]
        # Document is UPLOADED, not READY -> RESOURCE_CONFLICT (canonical machine).
        status, body = request("DELETE", f"{server_url}/api/v1/documents/{doc_id}", ADMIN)
        assert status == 409
        assert body["error"]["code"] == "RESOURCE_CONFLICT"


class TestDeniedPostDrainsBody:
    """Regression: a denied POST must not close the connection while the client
    is still sending its body. POST handlers authenticate before draining the
    body, so a denial was written and the socket closed with unread body bytes
    pending - a client mid-body then hit an aborted connection (WinError 10053
    on Windows), a load-dependent flake. The raw-socket client below sends
    headers plus half the body, pauses, then finishes: with the drain in place
    the server waits for the rest and the denial arrives cleanly."""

    PATH = "/api/v1/documents"
    BODY = {"filename": "a.csv", "content_base64": b64(b"a,b 1,2 ")}

    def test_denied_post_mid_body_still_gets_clean_response(self, server_url):
        base = server_url
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
