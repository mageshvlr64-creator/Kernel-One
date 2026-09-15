"""Tests for the OCR feature group (features/11_ocr) inside document-pipeline.

Coverage per feature docs §24/§25: one test per Failure-modes row, the full success
path (scanned PDF -> EXTRACTING -> OCR -> INDEXING), permission tests per role, the
exactly-one-audit-event invariant, and the failures/22 flagging semantics.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from document_pipeline import pdf as pdf_mod
from document_pipeline import ocr as ocr_mod
from document_pipeline.ocr import StubOcrEngine, embed_page_text
from document_pipeline.ocr_ops import OcrService, execute_ocr
from document_pipeline.ops import Context, OpError
from tests.conftest import make_pdf, service, b64  # noqa: F401

ANALYST = "dev-token-analyst"


@pytest.fixture()
def ocr(service):
    return OcrService(service)


def _upload_scanned_pdf(service, actor_token, pages=2):
    """Upload an image-only PDF (every page text-empty -> scanned candidate) and
    run it through detection so it sits in EXTRACTING with extraction cached."""
    from document_pipeline.ops import Context, execute
    from document_pipeline.policy import Actor

    actor = Actor(actor_id="dev:analyst", role="Analyst", clearance="INTERNAL",
                  workspace_id="ws-dev")
    ctx = Context(actor=actor)
    content = make_pdf(pages=pages, scanned=True)
    up = execute(service, ctx, "upload_validation",
                 {"filename": "scan.pdf", "content_base64": b64(content)})
    doc_id = up.resource_id
    execute(service, ctx, "file_type_detection", {"document_id": doc_id})
    execute(service, ctx, "native_pdf_parsing", {"document_id": doc_id})
    det = execute(service, ctx, "scanned_pdf_detection", {"document_id": doc_id})
    assert det.data["scanned"] is True
    return doc_id, ctx


def _analyst():
    from document_pipeline.policy import Actor
    return Actor(actor_id="dev:analyst", role="Analyst", clearance="INTERNAL",
                 workspace_id="ws-dev")


# --------------------------------------------------------------------- engine unit

class TestStubEngine:
    def test_reads_marker_payload_into_regions(self):
        png = embed_page_text("boiler drum level\nfeedwater valve")
        result = StubOcrEngine().recognize_page(png, page_number=1)
        assert len(result.regions) == 2
        assert result.regions[0].text == "boiler drum level"
        assert result.regions[0].bbox[0] < result.regions[0].bbox[2]
        assert 0.0 <= result.regions[0].confidence <= 1.0

    def test_transcribes_real_images_deterministically(self):
        # The stub's production contract: real rendered PNGs (the same input the
        # PaddleOCR adapter receives) produce deterministic pseudo-regions.
        png = b"\x89PNG-real-rendered-page-bytes"
        r1 = StubOcrEngine().recognize_page(png, 1)
        r2 = StubOcrEngine().recognize_page(png, 1)
        assert r1.regions and r1.text == r2.text  # deterministic
        assert r1.regions[0].text.startswith("ocr-stub page 1:")
        assert 0.0 <= r1.regions[0].confidence <= 1.0
        assert r1.regions[0].bbox[0] < r1.regions[0].bbox[2]
        # Different pixels -> different transcription (content-derived).
        r3 = StubOcrEngine().recognize_page(png + b"-varied", 1)
        assert r3.text != r1.text

    def test_reading_order_and_text_reconstruction(self):
        png = embed_page_text("line one\nline two\nline three")
        result = StubOcrEngine().recognize_page(png, page_number=3)
        assert result.text == "line one\nline two\nline three"
        ys = [r.bbox[1] for r in result.regions]
        assert ys == sorted(ys)


# --------------------------------------------------------------------- pipeline E2E

class TestOcrPipeline:
    def test_full_success_path_scanned_to_indexing(self, service, ocr):
        doc_id, ctx = _upload_scanned_pdf(service, ANALYST)
        assert service.store.get(doc_id).state == "EXTRACTING"

        r = execute_ocr(ocr, ctx, "page_processing", {"document_id": doc_id})
        assert r.state == "OCR"  # entered OCR state
        assert r.data["page_count"] >= 1

        r = execute_ocr(ocr, ctx, "text_reconstruction", {"document_id": doc_id})
        assert r.data["characters"] > 0

        r = execute_ocr(ocr, ctx, "complete_ocr", {"document_id": doc_id})
        assert r.state == "INDEXING"  # OCR -> INDEXING, hand-off to knowledge-fabric
        types = [e["event_type"] for e in service.audit.events]
        assert "document.ocr_completed" in types

    def test_page_processing_records_ocr_pages(self, service, ocr):
        doc_id, ctx = _upload_scanned_pdf(service, ANALYST)
        execute_ocr(ocr, ctx, "page_processing", {"document_id": doc_id})
        rows = ocr.pages.get(doc_id)
        assert len(rows) >= 1
        for row in rows:
            assert row["text"]
            assert row["bbox_regions"]
            assert row["engine"] == "stub"

    def test_ocr_requires_scanned_candidate(self, service, ocr):
        from document_pipeline.ops import Context, execute
        actor = _analyst()
        content = make_pdf(pages=1)  # native text PDF
        up = execute(service, Context(actor=actor), "upload_validation",
                     {"filename": "native.pdf", "content_base64": b64(content)})
        execute(service, Context(actor=actor), "file_type_detection",
                {"document_id": up.resource_id})
        execute(service, Context(actor=actor), "native_pdf_parsing",
                {"document_id": up.resource_id})
        with pytest.raises(OpError) as exc:
            execute_ocr(ocr, Context(actor=actor), "page_processing",
                        {"document_id": up.resource_id})
        assert exc.value.err.code == "INVALID_REQUEST"

    def test_ops_enforce_pipeline_order(self, service, ocr):
        doc_id, ctx = _upload_scanned_pdf(service, ANALYST)
        with pytest.raises(OpError) as exc:
            execute_ocr(ocr, ctx, "complete_ocr", {"document_id": doc_id})
        assert exc.value.err.code == "RESOURCE_CONFLICT"  # still EXTRACTING

    def test_low_confidence_pages_flagged_not_failed(self, service, ocr, monkeypatch):
        # Force every page's confidence below the threshold: pages are flagged,
        # still indexed, and complete_ocr still succeeds (failures/22).
        monkeypatch.setattr(ocr_mod, "_stable_confidence", lambda t, p: 0.10)
        doc_id, ctx = _upload_scanned_pdf(service, ANALYST)
        r = execute_ocr(ocr, ctx, "page_processing", {"document_id": doc_id})
        assert r.data["flagged_pages"] == r.data["page_count"]
        r = execute_ocr(ocr, ctx, "complete_ocr", {"document_id": doc_id})
        assert r.state == "INDEXING"
        rows = ocr.pages.get(doc_id)
        assert all(row["low_confidence"] for row in rows)
        assert all(row["flagged_reason"] for row in rows)

    def test_engine_down_fails_closed(self, service, ocr):
        class ExplodingEngine(StubOcrEngine):
            def recognize_page(self, image_png, page_number):
                raise Exception("engine crashed")

        ocr.engine = ExplodingEngine()
        doc_id, ctx = _upload_scanned_pdf(service, ANALYST)
        with pytest.raises(OpError) as exc:
            execute_ocr(ocr, ctx, "page_processing", {"document_id": doc_id})
        # A crashed engine is an execution failure; per failures/22 a fully-down
        # engine maps to DEPENDENCY_UNAVAILABLE. The dispatcher classifies both
        # out of INVALID_REQUEST — assert it is a 5xx-class registry code.
        assert exc.value.err.http_status >= 500


# --------------------------------------------------------------------- read ops

class TestOcrReadOps:
    def test_confidence_scores_report(self, service, ocr):
        doc_id, ctx = _upload_scanned_pdf(service, ANALYST)
        execute_ocr(ocr, ctx, "page_processing", {"document_id": doc_id})
        r = execute_ocr(ocr, ctx, "confidence_scores", {"document_id": doc_id})
        assert r.data["threshold"] == ocr_mod.LOW_CONFIDENCE_THRESHOLD
        assert r.data["pages"]

    def test_ocr_failures_lists_flagged(self, service, ocr, monkeypatch):
        monkeypatch.setattr(ocr_mod, "_stable_confidence", lambda t, p: 0.05)
        doc_id, ctx = _upload_scanned_pdf(service, ANALYST)
        execute_ocr(ocr, ctx, "page_processing", {"document_id": doc_id})
        r = execute_ocr(ocr, ctx, "ocr_failures", {"document_id": doc_id})
        assert len(r.data["flagged_pages"]) == r.data["pages_total"]

    def test_ocr_failures_before_ocr_is_invalid(self, service, ocr):
        doc_id, ctx = _upload_scanned_pdf(service, ANALYST)
        with pytest.raises(OpError) as exc:
            execute_ocr(ocr, ctx, "confidence_scores", {"document_id": doc_id})
        assert exc.value.err.code == "INVALID_REQUEST"

    def test_overview_and_engine_selection(self, service, ocr):
        doc_id, ctx = _upload_scanned_pdf(service, ANALYST)
        r = execute_ocr(ocr, ctx, "engine_selection", {"document_id": doc_id})
        assert r.data["engine"] == "stub"
        r = execute_ocr(ocr, ctx, "language_handling", {"document_id": doc_id})
        assert r.data["language"] == "en"
        r = execute_ocr(ocr, ctx, "ocr_overview", {"document_id": doc_id})
        assert r.data["pages_ocr"] == 0


# --------------------------------------------------------------------- contracts

class TestOcrContracts:
    def test_exactly_one_invocation_event_on_success(self, service, ocr):
        doc_id, ctx = _upload_scanned_pdf(service, ANALYST)
        before = len(service.audit.events)
        execute_ocr(ocr, ctx, "ocr_overview", {"document_id": doc_id})
        events = service.audit.events[before:]
        assert len(events) == 1
        assert events[0]["event_type"] == "ocr.ocr_overview"
        assert events[0]["result"] == "success"

    def test_exactly_one_invocation_event_on_error(self, service, ocr):
        doc_id, ctx = _upload_scanned_pdf(service, ANALYST)
        before = len(service.audit.events)
        with pytest.raises(OpError):
            execute_ocr(ocr, ctx, "confidence_scores", {"document_id": doc_id})
        events = service.audit.events[before:]
        assert len(events) == 1
        assert events[0]["event_type"] == "ocr.confidence_scores"
        assert events[0]["result"] == "error"
        assert events[0]["error_code"] == "INVALID_REQUEST"

    def test_denial_audited_with_role_and_rule(self, service, ocr):
        doc_id, ctx = _upload_scanned_pdf(service, ANALYST)
        from document_pipeline.policy import Actor
        auditor = Actor(actor_id="dev:auditor", role="Auditor", clearance="INTERNAL",
                        workspace_id="ws-dev")
        before = len(service.audit.events)
        with pytest.raises(OpError) as exc:
            execute_ocr(ocr, Context(actor=auditor), "page_processing",
                        {"document_id": doc_id})
        assert exc.value.err.code == "TOOL_NOT_ALLOWED"
        events = service.audit.events[before:]
        assert len(events) == 1
        assert events[0]["result"] == "denied"
        assert events[0]["actor_id"] == "dev:auditor"
        assert events[0]["reason"]

    @pytest.mark.parametrize("role,allowed", [
        ("Administrator", True), ("Security Officer", True), ("Operator", True),
        ("Analyst", True), ("Auditor", False), ("Restricted User", False)])
    def test_execute_permission_per_role(self, service, ocr, role, allowed):
        doc_id, _ = _upload_scanned_pdf(service, ANALYST)
        from document_pipeline.policy import Actor
        clearance = "PUBLIC" if role == "Restricted User" else "INTERNAL"
        actor = Actor(actor_id=f"dev:{role.lower().replace(' ', '-')}", role=role,
                      clearance=clearance, workspace_id="ws-dev")
        if allowed:
            r = execute_ocr(ocr, Context(actor=actor), "ocr_overview",
                            {"document_id": doc_id})
            assert r.status == "ok"
        else:
            with pytest.raises(OpError) as exc:
                execute_ocr(ocr, Context(actor=actor), "ocr_overview",
                            {"document_id": doc_id})
            if role == "Restricted User":
                # ocr_overview is a READ op: RestrictedUser is granted read by
                # role, but PUBLIC clearance < INTERNAL classification -> the
                # layered condition denies on classification, not role.
                assert exc.value.err.code == "FILE_CLASSIFICATION_DENIED"
            else:
                assert exc.value.err.code == "TOOL_NOT_ALLOWED"

    def test_unknown_op_rejected(self, service, ocr):
        doc_id, ctx = _upload_scanned_pdf(service, ANALYST)
        # Consistent with the ingestion dispatcher: an unknown op is a routing
        # error raised before any document/audit work happens.
        from document_pipeline.errors import RegistryError
        with pytest.raises(RegistryError) as exc:
            execute_ocr(ocr, ctx, "not_a_real_op", {"document_id": doc_id})
        assert exc.value.code == "INVALID_REQUEST"


# --------------------------------------------------------------------- HTTP API

@pytest.fixture()
def http_pair():
    """A live in-process server + its Api for direct route-handler tests."""
    import tempfile
    import threading

    from document_pipeline.api import Api, serve
    from document_pipeline.audit import InMemoryAuditSink
    from document_pipeline.config import Settings
    from document_pipeline.ops import DocumentIngestionService
    from document_pipeline.store import InMemoryDocumentStore
    from document_pipeline.storage import StubObjectStorage

    svc = DocumentIngestionService(store=InMemoryDocumentStore(),
                                   storage=StubObjectStorage(tempfile.mkdtemp()),
                                   audit_sink=InMemoryAuditSink(), settings=Settings())
    api = Api(svc)
    httpd = serve(api, "127.0.0.1", 0)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}", svc, api
    httpd.shutdown()


class TestOcrHttp:
    def test_ocr_route_roundtrip(self, http_pair):
        from document_pipeline.ops import Context, execute
        url, svc, api = http_pair
        actor = _analyst()
        content = make_pdf(pages=2, scanned=True)
        up = execute(svc, Context(actor=actor), "upload_validation",
                     {"filename": "scan.pdf", "content_base64": b64(content)})
        doc_id = up.resource_id
        for op in ("file_type_detection", "native_pdf_parsing",
                   "scanned_pdf_detection"):
            execute(svc, Context(actor=actor), op, {"document_id": doc_id})

        status, body = api.handle_ocr_op(actor, "page-processing",
                                         {"document_id": doc_id})
        assert status == 200 and body["data"]["state"] == "OCR"
        status, body = api.handle_ocr_op(actor, "complete-ocr",
                                         {"document_id": doc_id})
        assert status == 200 and body["data"]["state"] == "INDEXING"

    def test_ocr_route_unknown_slug(self, http_pair):
        url, svc, api = http_pair
        status, body = api.handle_ocr_op(_analyst(), "bogus-op", {})
        assert status == 400 and body["error"]["code"] == "INVALID_REQUEST"

    def test_ocr_route_denied_role(self, http_pair):
        from document_pipeline.ops import Context, execute
        from document_pipeline.policy import Actor
        url, svc, api = http_pair
        actor = _analyst()
        content = make_pdf(pages=1, scanned=True)
        up = execute(svc, Context(actor=actor), "upload_validation",
                     {"filename": "scan.pdf", "content_base64": b64(content)})
        auditor = Actor(actor_id="dev:auditor", role="Auditor", clearance="INTERNAL",
                        workspace_id="ws-dev")
        status, body = api.handle_ocr_op(auditor, "page-processing",
                                         {"document_id": up.resource_id})
        assert status == 403
