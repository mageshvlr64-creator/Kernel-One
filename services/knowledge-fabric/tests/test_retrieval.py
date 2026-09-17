from __future__ import annotations

import pytest

from tests.conftest import make_actor, make_document


def _index_document(service, analyst, classification="INTERNAL", workspace="ws-dev",
                   text=None):
    # Indexing actor must hold clearance >= the document's classification and match its
    # workspace (the policy gate enforces the matrix on every document-scoped call).
    actor = (analyst if classification == "INTERNAL" and workspace == "ws-dev"
             else make_actor("Administrator", clearance="RESTRICTED",
                             workspace=workspace))
    ref = make_document(service, classification=classification, workspace=workspace,
                        text=text, owner=actor.actor_id)
    for op in ("chunking", "embeddings", "vector_index"):
        service.invoke(op, actor, {"document_id": ref.document_id})
    return ref


class TestHybridSearch:
    def test_finds_relevant_document(self, service, analyst):
        _index_document(service, analyst,
                        text="Boiler drum level control uses three-element control. " * 8)
        result = service.invoke("hybrid_search", analyst,
                                {"query": "boiler drum level control"})
        assert result.data["hits"], "expected hits for indexed corpus"
        assert result.data["hits"][0]["score"] > 0
        assert "score_breakdown" in result.data["hits"][0]

    def test_unknown_query_returns_empty_hits(self, service, analyst):
        _index_document(service, analyst)
        result = service.invoke("hybrid_search", analyst,
                                {"query": "zeppelin quantum marmalade"})
        assert result.data["hits"] == []

    def test_missing_query_is_invalid_request(self, service, analyst):
        with pytest.raises(Exception) as exc:
            service.invoke("hybrid_search", analyst, {})
        assert getattr(exc.value, "code", "") == "INVALID_REQUEST"

    def test_top_k_bounds(self, service, analyst):
        _index_document(service, analyst)
        with pytest.raises(Exception) as exc:
            service.invoke("hybrid_search", analyst,
                           {"query": "pump", "top_k": 999})
        assert getattr(exc.value, "code", "") == "INVALID_REQUEST"

    def test_classification_filter_hides_confidential(self, service, analyst):
        _index_document(service, analyst, classification="CONFIDENTIAL",
                        text="Secret reactor design parameters and signatures. " * 8)
        _index_document(service, analyst, classification="INTERNAL",
                        text="Public pump maintenance checklist steps. " * 8)
        result = service.invoke("hybrid_search", analyst,
                                {"query": "reactor design parameters"})
        assert all("reactor" not in h["text"].lower() or
                   h["document_name"] != "" for h in result.data["hits"])
        # The confidential doc's chunks must not appear at all.
        confidential_hits = [h for h in result.data["hits"]
                             if "Secret reactor" in h["text"]]
        assert confidential_hits == []

    def test_elevated_clearance_sees_confidential(self, service):
        _index_document(service, None, classification="CONFIDENTIAL",
                        text="Secret reactor design parameters and signatures. " * 8)
        admin_rest = make_actor("Administrator", clearance="RESTRICTED")
        result = service.invoke("hybrid_search", admin_rest,
                                {"query": "reactor design parameters"})
        assert any("Secret reactor" in h["text"] for h in result.data["hits"])

    def test_auditor_denied_corpus_read(self, service, auditor, analyst):
        # Canonical matrix row Document:read — Auditor column is ❌ (reference/05).
        _index_document(service, analyst,
                        text="Turbine vibration monitoring thresholds. " * 8)
        with pytest.raises(Exception) as exc:
            service.invoke("hybrid_search", auditor, {"query": "turbine vibration"})
        assert getattr(exc.value, "code", "") == "TOOL_NOT_ALLOWED"


class TestReranking:
    def test_coverage_boost_reorders(self, service, analyst):
        payload = {
            "query": "boiler drum level",
            "candidates": [
                {"chunk_id": "a", "text": "boiler drum level control loop",
                 "score": 0.4},
                {"chunk_id": "b", "text": "drum level is critical in boilers",
                 "score": 0.45},
                {"chunk_id": "c", "text": "unrelated text about calendars",
                 "score": 0.9},
            ],
        }
        result = service.invoke("reranking", analyst, payload)
        scores = {h["chunk_id"]: h["score"] for h in result.data["hits"]}
        # 0.5*base + 0.5*coverage: 'a' covers 3/4 query tokens, 'c' covers 1/4.
        assert scores["a"] > scores["c"]

    def test_candidates_validated(self, service, analyst):
        with pytest.raises(Exception) as exc:
            service.invoke("reranking", analyst, {"query": "x", "candidates": "nope"})
        assert getattr(exc.value, "code", "") == "INVALID_REQUEST"


class TestContextAssembly:
    def test_budget_truncation(self, service, analyst):
        _index_document(service, analyst, text="Long procedure text. " * 400)
        result = service.invoke("context_assembly", analyst,
                                {"query": "procedure", "top_k": 5,
                                 "max_tokens": 64})
        assert result.data["total_tokens_approx"] <= 64
        assert result.data["truncated"] in (True, False)

    def test_min_budget_enforced(self, service, analyst):
        with pytest.raises(Exception) as exc:
            service.invoke("context_assembly", analyst,
                           {"query": "x", "max_tokens": 1})
        assert getattr(exc.value, "code", "") == "INVALID_REQUEST"


class TestPermissionFiltering:
    def test_hidden_classified_document(self, service, analyst):
        other = make_document(service, classification="RESTRICTED")
        result = service.invoke("permission_filtering", analyst,
                                {"document_ids": [other.document_id]})
        assert result.data["visible"] == []
        assert result.data["hidden"][0]["reason"].startswith("classification")

    def test_admin_carveout_sees_other_workspace(self, service, admin, analyst):
        other = make_document(service, workspace="ws-other")
        result = service.invoke("permission_filtering", admin,
                                {"document_ids": [other.document_id]})
        assert result.data["visible"] and not result.data["hidden"]

    def test_non_admin_hidden_from_other_workspace(self, service, analyst):
        other = make_document(service, workspace="ws-other")
        result = service.invoke("permission_filtering", analyst,
                                {"document_ids": [other.document_id]})
        assert result.data["hidden"] and "workspace" in result.data["hidden"][0]["reason"]


class TestOverviewQualityFailures:
    def test_overview_counts(self, service, analyst):
        _index_document(service, analyst)
        result = service.invoke("knowledge_overview", analyst, {})
        assert result.data["documents_indexed"] >= 1
        assert result.data["total_chunks"] >= 1

    def test_overview_unknown_document_404(self, service, analyst):
        import uuid
        with pytest.raises(Exception) as exc:
            service.invoke("knowledge_overview", analyst,
                           {"document_id": str(uuid.uuid4())})
        assert getattr(exc.value, "code", "") == "FILE_NOT_FOUND"

    def test_quality_metrics_shape(self, service, analyst):
        _index_document(service, analyst,
                        text="Alignment tolerance for coupling bolts. " * 8)
        result = service.invoke("retrieval_quality", analyst,
                                {"query": "alignment tolerance"})
        assert {"hit_count", "score_max", "score_mean", "empty_result"} <= \
            set(result.data.keys())

    def test_failures_diagnoses_empty_index(self, service, analyst):
        result = service.invoke("retrieval_failures", analyst,
                                {"query": "anything"})
        assert "no_chunks_indexed" in result.data["diagnosis"]

    def test_failures_diagnoses_no_overlap(self, service, analyst):
        _index_document(service, analyst, text="Conveyor belt speed limits. " * 8)
        result = service.invoke("retrieval_failures", analyst,
                                {"query": "quantum marmalade zeppelin"})
        assert "no_keyword_overlap" in result.data["diagnosis"] or \
            "no_score_above_threshold" in result.data["diagnosis"]
