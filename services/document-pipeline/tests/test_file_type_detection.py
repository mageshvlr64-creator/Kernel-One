"""File Type Detection tests — feature file 03 (§24/§25 coverage).

Note: the real EICAR test string is quarantined by Windows Defender the moment the storage
stub writes it to disk (which is itself proof the check matters), so these tests inject a
harmless signature via monkeypatch to exercise the same code path deterministically.
"""
from __future__ import annotations

import pytest

from document_pipeline.ops import OpError

from .conftest import b64, make_pdf, pdf_payload, text_payload

BAIT = b"hello DEFENDER-BAIT-SIGNATURE world"  # text-decodable, upload-accepted


@pytest.fixture()
def bait_signature(monkeypatch):
    monkeypatch.setattr("document_pipeline.ops._MALWARE_SIGNATURES",
                        (b"DEFENDER-BAIT-SIGNATURE",))


class TestSuccessPath:
    def test_uploaded_to_extracting(self, call, actors):
        up = call(actors["analyst"], "upload_validation", text_payload(actors))
        result = call(actors["analyst"], "file_type_detection",
                      {"document_id": up.resource_id})
        assert result.status == "ok"
        assert result.state == "EXTRACTING"

    def test_pdf_passes_validation(self, call, actors):
        up = call(actors["analyst"], "upload_validation",
                  pdf_payload(actors, make_pdf()))
        result = call(actors["analyst"], "file_type_detection",
                      {"document_id": up.resource_id})
        assert result.state == "EXTRACTING"


class TestFailureModes:
    def test_malware_signature_moves_document_to_failed(self, call, actors,
                                                        bait_signature):
        up = call(actors["analyst"], "upload_validation",
                  {"filename": "bait.txt", "content_base64": b64(BAIT)})
        with pytest.raises(OpError) as err:
            call(actors["analyst"], "file_type_detection",
                 {"document_id": up.resource_id})
        assert err.value.err.code == "INVALID_REQUEST"
        assert "malware" in err.value.err.operator_detail
        meta = call(actors["analyst"], "metadata_extraction",
                    {"document_id": up.resource_id})
        assert meta.data["metadata"]["state"] == "FAILED"

    def test_failed_document_has_specific_reason_audited(self, call, actors, audit_sink,
                                                         bait_signature):
        up = call(actors["analyst"], "upload_validation",
                  {"filename": "bait.txt", "content_base64": b64(BAIT)})
        with pytest.raises(OpError):
            call(actors["analyst"], "file_type_detection",
                 {"document_id": up.resource_id})
        failed = [e for e in audit_sink.events if e["event_type"] == "document.failed"]
        assert len(failed) == 1
        assert failed[0]["error_code"] == "INVALID_REQUEST"
        assert "malware" in failed[0]["reason"]

    def test_wrong_state_is_resource_conflict(self, call, actors):
        up = call(actors["analyst"], "upload_validation", text_payload(actors))
        call(actors["analyst"], "file_type_detection", {"document_id": up.resource_id})
        # Second run: document is EXTRACTING, not UPLOADED -> RESOURCE_CONFLICT.
        with pytest.raises(OpError) as err:
            call(actors["analyst"], "file_type_detection",
                 {"document_id": up.resource_id})
        assert err.value.err.code == "RESOURCE_CONFLICT"

    def test_unknown_document_is_file_not_found(self, call, actors):
        with pytest.raises(OpError) as err:
            call(actors["analyst"], "file_type_detection",
                 {"document_id": str(__import__("uuid").uuid4())})
        assert err.value.err.code == "FILE_NOT_FOUND"


class TestPermissions:
    def test_auditor_cannot_execute(self, call, actors):
        up = call(actors["analyst"], "upload_validation", text_payload(actors))
        with pytest.raises(OpError) as err:
            call(actors["auditor"], "file_type_detection",
                 {"document_id": up.resource_id})
        assert err.value.err.code == "TOOL_NOT_ALLOWED"

    def test_below_clearance_read_of_document_denied(self, call, actors):
        up = call(actors["administrator"], "upload_validation",
                  text_payload(actors, classification="RESTRICTED"))
        with pytest.raises(OpError) as err:
            call(actors["analyst"], "file_type_detection",
                 {"document_id": up.resource_id})
        assert err.value.err.code == "FILE_CLASSIFICATION_DENIED"
