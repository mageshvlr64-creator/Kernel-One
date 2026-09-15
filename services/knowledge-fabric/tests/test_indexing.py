from __future__ import annotations

import uuid

import pytest

from tests.conftest import make_actor, make_document


class TestChunking:
    def test_happy_path_chunks_created(self, service, analyst):
        ref = make_document(service)
        result = service.invoke("chunking", analyst, {"document_id": ref.document_id})
        assert result.data["chunk_count"] >= 1
        chunks = service.index.chunks_for_document(ref.document_id)
        assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
        assert all(c.text.strip() for c in chunks)

    def test_unknown_document_404_shape(self, service, analyst):
        with pytest.raises(Exception) as exc:
            service.invoke("chunking", analyst,
                           {"document_id": str(uuid.uuid4())})
        assert getattr(exc.value, "code", "") == "FILE_NOT_FOUND"
        assert getattr(exc.value, "http_status", 0) == 404

    def test_document_not_in_indexing_state_rejected(self, service, analyst):
        ref = make_document(service, state="READY")
        with pytest.raises(Exception) as exc:
            service.invoke("chunking", analyst, {"document_id": ref.document_id})
        assert getattr(exc.value, "code", "") == "INVALID_REQUEST"

    def test_empty_text_moves_document_to_failed(self, service, analyst):
        ref = make_document(service, text="   \n  ")
        with pytest.raises(Exception) as exc:
            service.invoke("chunking", analyst, {"document_id": ref.document_id})
        assert getattr(exc.value, "code", "") == "INVALID_REQUEST"
        assert ref.state == "FAILED"
        # The document.failed transition event was emitted alongside the op event.
        types = [e["event_type"] for e in service.audit_sink.events]
        assert "document.failed" in types

    def test_rechunking_is_idempotent(self, service, analyst):
        ref = make_document(service)
        first = service.invoke("chunking", analyst, {"document_id": ref.document_id})
        second = service.invoke("chunking", analyst, {"document_id": ref.document_id})
        assert first.data["chunk_count"] == second.data["chunk_count"]
        total = service.index.count_for_document(ref.document_id)
        assert total == first.data["chunk_count"]


class TestEmbeddingsAndIndex:
    def test_embeddings_fill_all_chunks(self, service, analyst):
        ref = make_document(service)
        service.invoke("chunking", analyst, {"document_id": ref.document_id})
        result = service.invoke("embeddings", analyst, {"document_id": ref.document_id})
        chunks = service.index.chunks_for_document(ref.document_id)
        assert result.data["embedded_count"] == len(chunks)
        assert all(c.embedding and len(c.embedding) == 768 for c in chunks)

    def test_embeddings_before_chunking_fails(self, service, analyst):
        ref = make_document(service)
        with pytest.raises(Exception) as exc:
            service.invoke("embeddings", analyst, {"document_id": ref.document_id})
        assert getattr(exc.value, "code", "") == "INVALID_REQUEST"

    def test_vector_index_requires_embeddings(self, service, analyst):
        ref = make_document(service)
        service.invoke("chunking", analyst, {"document_id": ref.document_id})
        with pytest.raises(Exception) as exc:
            service.invoke("vector_index", analyst, {"document_id": ref.document_id})
        assert getattr(exc.value, "code", "") == "INVALID_REQUEST"

    def test_full_pipeline_moves_document_to_ready(self, service, analyst):
        ref = make_document(service)
        for op in ("chunking", "embeddings", "keyword_index", "vector_index"):
            service.invoke(op, analyst, {"document_id": ref.document_id})
        assert ref.state == "READY"
        types = [e["event_type"] for e in service.audit_sink.events]
        assert "document.indexed" in types

    def test_state_machine_rejects_indexing_on_non_indexing_doc(self, service, analyst):
        ref = make_document(service, state="UPLOADED")
        with pytest.raises(Exception) as exc:
            service.invoke("chunking", analyst, {"document_id": ref.document_id})
        assert getattr(exc.value, "code", "") == "INVALID_REQUEST"
        assert ref.state == "UPLOADED"  # untouched


class TestNormalization:
    def test_nfkc_and_whitespace_collapse(self, service, analyst):
        ref = make_document(service, text="ﬁle  name\u00A0 with   spaces\n\nnext")
        result = service.invoke("document_normalization", analyst,
                                {"document_id": ref.document_id})
        assert result.data["normalized_chars"] > 0
        assert "ﬁ" not in ref.source_text  # ligature decomposed
        assert "  " not in ref.source_text


class TestIndexes:
    def test_keyword_index_counts_terms(self, service, analyst):
        ref = make_document(service)
        service.invoke("chunking", analyst, {"document_id": ref.document_id})
        result = service.invoke("keyword_index", analyst,
                                {"document_id": ref.document_id})
        assert result.data["terms_indexed"] > 0

    def test_metadata_index_after_ready(self, service, analyst):
        ref = make_document(service)
        for op in ("chunking", "embeddings", "vector_index"):
            service.invoke(op, analyst, {"document_id": ref.document_id})
        # Legal after READY (idempotent bookkeeping) — no 400.
        result = service.invoke("metadata_index", analyst,
                                {"document_id": ref.document_id})
        assert "metadata_entries" in result.data
