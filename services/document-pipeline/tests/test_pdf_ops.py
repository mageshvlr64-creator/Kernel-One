"""Native PDF Parsing / Scanned Detection / Page & Metadata Extraction / Overview tests —
feature files 04-07 + 01 (§24/§25 coverage), failures/21_pdf_failures.md."""
from __future__ import annotations

import uuid

import pytest

from document_pipeline.ops import OpError

from .conftest import b64, make_pdf, pdf_payload, run_pdf_pipeline, text_payload


def _encrypted_pdf() -> bytes:
    import pymupdf
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 100), "classified content")
    return doc.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256,
                       owner_pw="pw", user_pw="pw")


class TestNativePdfParsing:
    def test_success_parses_pages_and_keeps_state(self, call, actors):
        run = run_pdf_pipeline(call, actors["analyst"], make_pdf(pages=3))
        parsed = run["parsed"]
        assert parsed.data["page_count"] == 3
        assert parsed.data["routed_to"] == "INDEXING"
        assert parsed.data["scanned_candidate"] is False
        # EXTRACTING -> INDEXING is owned by the knowledge fabric (group 13): not applied.
        assert parsed.data["transition_applied"] is False
        assert parsed.state == "EXTRACTING"

    def test_password_protected_pdf_fails_specific(self, call, actors, audit_sink):
        up = call(actors["analyst"], "upload_validation",
                  pdf_payload(actors, _encrypted_pdf()))
        call(actors["analyst"], "file_type_detection", {"document_id": up.resource_id})
        with pytest.raises(OpError) as err:
            call(actors["analyst"], "native_pdf_parsing",
                 {"document_id": up.resource_id})
        assert err.value.err.code == "INVALID_REQUEST"
        assert "password-protected" in err.value.err.operator_detail
        # failures/21: state -> FAILED with the specific reason, audited.
        failed = [e for e in audit_sink.events if e["event_type"] == "document.failed"]
        assert len(failed) == 1
        assert "password-protected" in failed[0]["reason"]
        assert failed[0]["error_code"] == "INVALID_REQUEST"
        meta = call(actors["analyst"], "metadata_extraction",
                    {"document_id": up.resource_id})
        assert meta.data["metadata"]["state"] == "FAILED"

    def test_failed_document_rejects_further_parse_ops(self, call, actors):
        up = call(actors["analyst"], "upload_validation",
                  pdf_payload(actors, _encrypted_pdf()))
        call(actors["analyst"], "file_type_detection", {"document_id": up.resource_id})
        with pytest.raises(OpError):
            call(actors["analyst"], "native_pdf_parsing",
                 {"document_id": up.resource_id})
        # Document is now FAILED, no longer EXTRACTING -> RESOURCE_CONFLICT.
        with pytest.raises(OpError) as err:
            call(actors["analyst"], "native_pdf_parsing",
                 {"document_id": up.resource_id})
        assert err.value.err.code == "RESOURCE_CONFLICT"

    def test_corrupted_pdf_fails_invalid_request(self, call, actors):
        up = call(actors["analyst"], "upload_validation",
                  pdf_payload(actors, b"%PDF-1.4 this is not really a pdf"))
        call(actors["analyst"], "file_type_detection", {"document_id": up.resource_id})
        with pytest.raises(OpError) as err:
            call(actors["analyst"], "native_pdf_parsing",
                 {"document_id": up.resource_id})
        assert err.value.err.code == "INVALID_REQUEST"
        meta = call(actors["analyst"], "metadata_extraction",
                    {"document_id": up.resource_id})
        assert meta.data["metadata"]["state"] == "FAILED"

    def test_non_pdf_document_rejected(self, call, actors):
        up = call(actors["analyst"], "upload_validation", text_payload(actors))
        call(actors["analyst"], "file_type_detection", {"document_id": up.resource_id})
        with pytest.raises(OpError) as err:
            call(actors["analyst"], "native_pdf_parsing",
                 {"document_id": up.resource_id})
        assert err.value.err.code == "INVALID_REQUEST"
        assert "requires a PDF" in err.value.err.operator_detail

    def test_requires_extracting_state(self, call, actors):
        up = call(actors["analyst"], "upload_validation", pdf_payload(actors, make_pdf()))
        # Document is UPLOADED; op requires EXTRACTING.
        with pytest.raises(OpError) as err:
            call(actors["analyst"], "native_pdf_parsing",
                 {"document_id": up.resource_id})
        assert err.value.err.code == "RESOURCE_CONFLICT"

    def test_exactly_one_invocation_event_on_success(self, call, actors, audit_sink):
        run_pdf_pipeline(call, actors["analyst"], make_pdf())
        events = [e for e in audit_sink.events
                  if e["event_type"] == "document_ingestion.native_pdf_parsing"]
        assert len(events) == 1
        assert events[0]["result"] == "success"

    def test_no_outbound_network_calls_by_construction(self):
        """Acceptance criterion: no outbound network call occurs during execution.
        The only third-party import is pymupdf, which parses in-memory bytes."""
        import document_pipeline.pdf as pdf_mod
        from pathlib import Path
        source = Path(pdf_mod.__file__).read_text(encoding="utf-8")
        assert "requests" not in source and "urllib" not in source
        assert "http.client" not in source and "socket" not in source


class TestScannedPdfDetection:
    def test_native_text_pdf_is_not_scanned(self, call, actors):
        run = run_pdf_pipeline(call, actors["analyst"], make_pdf(pages=2))
        result = call(actors["analyst"], "scanned_pdf_detection",
                      {"document_id": run["document_id"]})
        assert result.data["scanned"] is False
        assert result.data["text_empty_pages"] == []

    def test_scanned_pdf_detected_and_routed_to_ocr(self, call, actors):
        run = run_pdf_pipeline(call, actors["analyst"],
                               make_pdf(pages=2, scanned=True))
        result = call(actors["analyst"], "scanned_pdf_detection",
                      {"document_id": run["document_id"]})
        assert result.data["scanned"] is True
        assert result.data["text_empty_pages"] == [1, 2]
        parsed = run["parsed"]
        assert parsed.data["routed_to"] == "OCR"
        # OCR transition (EXTRACTING -> OCR) is owned by feature group 11: not applied.
        assert parsed.state == "EXTRACTING"

    def test_non_pdf_rejected(self, call, actors):
        up = call(actors["analyst"], "upload_validation", text_payload(actors))
        call(actors["analyst"], "file_type_detection", {"document_id": up.resource_id})
        with pytest.raises(OpError) as err:
            call(actors["analyst"], "scanned_pdf_detection",
                 {"document_id": up.resource_id})
        assert err.value.err.code == "INVALID_REQUEST"


class TestPageAndMetadataExtraction:
    def test_page_extraction_pdf(self, call, actors):
        run = run_pdf_pipeline(call, actors["analyst"], make_pdf(pages=2))
        result = call(actors["analyst"], "page_extraction",
                      {"document_id": run["document_id"]})
        pages = result.data["pages"]
        assert len(pages) == 2
        assert [p["page_number"] for p in pages] == [1, 2]
        assert all(p["characters"] > 0 for p in pages)

    def test_page_extraction_text_document(self, call, actors):
        up = call(actors["analyst"], "upload_validation", text_payload(actors))
        call(actors["analyst"], "file_type_detection", {"document_id": up.resource_id})
        result = call(actors["analyst"], "page_extraction",
                      {"document_id": up.resource_id})
        assert result.data["pages"][0]["page_number"] == 1

    def test_metadata_extraction_pdf(self, call, actors):
        run = run_pdf_pipeline(call, actors["analyst"], make_pdf(pages=2))
        result = call(actors["analyst"], "metadata_extraction",
                      {"document_id": run["document_id"]})
        md = result.data["metadata"]
        assert md["mime_type"] == "application/pdf"
        assert md["page_count"] == 2
        assert md["sha256"]
        assert md["classification"] == "INTERNAL"
        assert md["authority"] == "secondary"
        assert md["scanned_candidate"] is False

    def test_metadata_includes_knowledge_trust_fields(self, call, actors):
        up = call(actors["analyst"], "upload_validation",
                  text_payload(actors, authority="primary"))
        result = call(actors["analyst"], "metadata_extraction",
                      {"document_id": up.resource_id})
        assert result.data["metadata"]["authority"] == "primary"


class TestIngestionOverview:
    def test_overview_reflects_pipeline_progress(self, call, actors):
        run = run_pdf_pipeline(call, actors["analyst"], make_pdf())
        result = call(actors["analyst"], "ingestion_overview",
                      {"document_id": run["document_id"]})
        stages = result.data["stages"]
        assert stages["uploaded"] is True
        assert stages["validated_or_later"] is True
        assert stages["extracting_or_later"] is True
        assert stages["ready"] is False
        assert stages["failed"] is False

    def test_overview_read_action_as_restricted_user(self, call, actors):
        up = call(actors["analyst"], "upload_validation", text_payload(actors))
        result = call(actors["restricted"], "ingestion_overview",
                      {"document_id": up.resource_id})
        assert result.status == "ok"  # read is granted to Restricted User per matrix

    def test_auditor_cannot_read_documents(self, call, actors):
        up = call(actors["analyst"], "upload_validation", text_payload(actors))
        with pytest.raises(OpError) as err:
            call(actors["auditor"], "ingestion_overview",
                 {"document_id": up.resource_id})
        assert err.value.err.code == "TOOL_NOT_ALLOWED"


class TestPdfAdapterUnit:
    def test_spans_carry_bboxes(self):
        from document_pipeline import pdf as pdf_mod
        outcome = pdf_mod.parse_pdf(make_pdf(pages=1))
        page = outcome.pages[0]
        assert page.spans and all(len(s.bbox) == 4 for s in page.spans)
        assert page.spans[0].text.strip()

    def test_parse_of_garbage_raises_specific_error(self):
        from document_pipeline import pdf as pdf_mod
        with pytest.raises(pdf_mod.PdfParseError):
            pdf_mod.parse_pdf(b"definitely not a pdf at all")
