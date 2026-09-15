"""Upload Validation tests — feature file 02 (§24/§25 coverage)."""
from __future__ import annotations

import base64

import pytest

from document_pipeline.ops import OpError
from document_pipeline.policy import Actor

from .conftest import FailingStorage, b64, make_pdf, pdf_payload, text_payload


class TestSuccessPath:
    def test_upload_creates_document_in_uploaded_state(self, call, actors):
        result = call(actors["analyst"], "upload_validation",
                      text_payload(actors))
        assert result.status == "ok"
        assert result.state == "UPLOADED"
        assert result.resource_id
        assert result.audit_event_id

    def test_upload_returns_canonical_outputs_shape(self, call, actors):
        result = call(actors["analyst"], "upload_validation", text_payload(actors))
        assert set(result.__dataclass_fields__) == {
            "status", "resource_id", "state", "audit_event_id", "timestamp", "data"}

    def test_mime_detected_server_side_not_from_client(self, call, actors):
        # Client claims pdf; content is text -> server detects text/csv (not the header).
        payload = text_payload(actors, content="a,b\n1,2\n", mime_type="application/pdf")
        result = call(actors["analyst"], "upload_validation", payload)
        meta = call(actors["analyst"], "metadata_extraction",
                    {"document_id": result.resource_id})
        assert meta.data["metadata"]["mime_type"] == "text/csv"

    def test_pdf_upload_detected_as_pdf(self, call, actors):
        result = call(actors["analyst"], "upload_validation",
                      pdf_payload(actors, make_pdf()))
        meta = call(actors["analyst"], "metadata_extraction",
                    {"document_id": result.resource_id})
        assert meta.data["metadata"]["mime_type"] == "application/pdf"


class TestFailureModes:
    def test_invalid_request_missing_payload(self, call, actors):
        with pytest.raises(OpError) as err:
            call(actors["analyst"], "upload_validation", {})
        assert err.value.err.code == "INVALID_REQUEST"
        assert err.value.err.http_status == 400

    def test_invalid_base64_rejected(self, call, actors):
        payload = {"filename": "x.txt", "content_base64": "!!!not-base64!!!"}
        with pytest.raises(OpError) as err:
            call(actors["analyst"], "upload_validation", payload)
        assert err.value.err.code == "INVALID_REQUEST"
        assert any(f["field"] == "content_base64"
                   for f in err.value.err.details)

    def test_empty_file_rejected(self, call, actors):
        with pytest.raises(OpError) as err:
            call(actors["analyst"], "upload_validation",
                 text_payload(actors, content=""))
        assert err.value.err.code == "INVALID_REQUEST"

    def test_unsupported_binary_rejected_before_state(self, call, actors, audit_sink):
        exe = b"MZ\x90\x00" + b"\x00" * 100
        with pytest.raises(OpError) as err:
            call(actors["analyst"], "upload_validation",
                 {"filename": "tool.exe", "content_base64": b64(exe)})
        assert err.value.err.code == "INVALID_REQUEST"
        assert "does not match any supported type" in err.value.err.operator_detail

    def test_size_limit_enforced(self, service, call, actors):
        from document_pipeline.config import Settings
        service.settings = Settings(max_upload_size_bytes=10)
        with pytest.raises(OpError) as err:
            call(actors["analyst"], "upload_validation",
                 text_payload(actors, content="x" * 11))
        assert err.value.err.code == "INVALID_REQUEST"
        assert any("maximum upload size" in f["message"]
                   for f in err.value.err.details)

    def test_dependency_unavailable_when_storage_down(self, service, call, actors,
                                                      monkeypatch):
        service.storage = FailingStorage()
        monkeypatch.setattr("document_pipeline.retry.BACKOFF_SECONDS", 0)
        with pytest.raises(OpError) as err:
            call(actors["analyst"], "upload_validation", text_payload(actors))
        assert err.value.err.code == "DEPENDENCY_UNAVAILABLE"
        assert err.value.err.http_status == 503
        assert service.storage.calls == 2  # initial + 1 retry per runtime/11

    def test_failure_produces_exactly_one_invocation_event(self, call, actors, audit_sink):
        with pytest.raises(OpError):
            call(actors["analyst"], "upload_validation", {})
        events = [e for e in audit_sink.events
                  if e["event_type"] == "document_ingestion.upload_validation"]
        assert len(events) == 1
        assert events[0]["result"] == "error"
        assert events[0]["error_code"] == "INVALID_REQUEST"


class TestDedup:
    def test_same_content_same_workspace_deduplicated(self, call, actors, audit_sink):
        first = call(actors["analyst"], "upload_validation", text_payload(actors))
        second = call(actors["analyst"], "upload_validation", text_payload(actors))
        assert second.resource_id == first.resource_id
        assert second.data.get("deduplicated") is True
        # Two invocations -> exactly two invocation events, one document created.
        inv = [e for e in audit_sink.events
               if e["event_type"] == "document_ingestion.upload_validation"]
        assert len(inv) == 2
        assert len(audit_sink.events) == 3  # 2 invocation + 1 document.uploaded

    def test_same_content_different_classification_rejected_after_dedup_check(
            self, call, actors):
        call(actors["analyst"], "upload_validation", text_payload(actors))
        # Same content but CONFIDENTIAL -> analyst (clearance INTERNAL) is denied.
        with pytest.raises(OpError) as err:
            call(actors["analyst"], "upload_validation",
                 text_payload(actors, classification="CONFIDENTIAL"))
        assert err.value.err.code == "FILE_CLASSIFICATION_DENIED"


class TestPermissions:
    def test_auditor_cannot_upload(self, call, actors, audit_sink):
        with pytest.raises(OpError) as err:
            call(actors["auditor"], "upload_validation", text_payload(actors))
        assert err.value.err.code == "TOOL_NOT_ALLOWED"
        assert err.value.err.http_status == 403
        inv = [e for e in audit_sink.events
               if e["event_type"] == "document_ingestion.upload_validation"]
        assert len(inv) == 1 and inv[0]["result"] == "denied"

    def test_below_clearance_classified_upload_denied(self, call, actors):
        with pytest.raises(OpError) as err:
            call(actors["analyst"], "upload_validation",
                 text_payload(actors, classification="RESTRICTED"))
        assert err.value.err.code == "FILE_CLASSIFICATION_DENIED"

    def test_admin_above_clearance_uploads(self, call, actors):
        result = call(actors["administrator"], "upload_validation",
                      text_payload(actors, classification="RESTRICTED"))
        assert result.status == "ok"


class TestAudit:
    def test_success_event_conforms_to_canonical_schema(self, call, actors, audit_sink):
        call(actors["analyst"], "upload_validation", text_payload(actors))
        event = next(e for e in audit_sink.events
                     if e["event_type"] == "document_ingestion.upload_validation")
        from document_pipeline.audit import REQUIRED_FIELDS
        for field in REQUIRED_FIELDS:
            assert field in event
        assert event["action"] == "create"
        assert event["resource_type"] == "Document"
        assert event["result"] == "success"
        assert event["prev_event_hash"]  # chain present
