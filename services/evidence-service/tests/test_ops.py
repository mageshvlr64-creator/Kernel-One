from __future__ import annotations

import pytest

from tests.conftest import (CHUNK_ID, DOC_ID, TASK_ID, create_evidence,
                            evidence_payload, make_actor, make_answer_text,
                            seed_chain, seed_chunk)


class TestEvidenceSystem:
    def test_create_success_shape(self, service, analyst):
        result = create_evidence(service, analyst)
        ev = result.data["evidence"]
        assert ev["source_document_id"] == DOC_ID
        assert ev["document_version"] == 1
        assert ev["verification_status"] == "unverified"  # domain/13 default
        assert ev["retrieval_method"] == "hybrid"
        assert ev["id"] == result.resource_id

    def test_created_rows_always_start_unverified(self, service, analyst):
        # A caller cannot set verification_status at create time; only op 09 writes it.
        result = service.invoke("evidence_system", analyst,
                                evidence_payload(verification_status="supported"))
        assert result.data["evidence"]["verification_status"] == "unverified"

    @pytest.mark.parametrize("field,issue", [
        ("task_id", None),
        ("source_document_id", None),
        ("chunk_id", None),
        ("document_version", None),
        ("source_hash", None),
        ("retrieval_method", None),
        ("source_authority", None),
    ])
    def test_missing_required_field_rejected(self, service, analyst, field, issue):
        payload = evidence_payload()
        payload.pop(field)
        with pytest.raises(Exception) as exc:
            service.invoke("evidence_system", analyst, payload)
        assert getattr(exc.value, "code", "") == "INVALID_REQUEST"

    def test_bad_source_hash_format_rejected(self, service, analyst):
        with pytest.raises(Exception) as exc:
            service.invoke("evidence_system", analyst,
                           evidence_payload(source_hash="deadbeef"))
        assert getattr(exc.value, "code", "") == "INVALID_REQUEST"
        details = exc.value.details
        assert any(d["field"] == "source_hash" for d in details)

    def test_confidence_bounds_enforced(self, service, analyst):
        with pytest.raises(Exception) as exc:
            service.invoke("evidence_system", analyst, evidence_payload(confidence=1.5))
        assert getattr(exc.value, "code", "") == "INVALID_REQUEST"

    def test_document_version_must_be_positive(self, service, analyst):
        with pytest.raises(Exception) as exc:
            service.invoke("evidence_system", analyst, evidence_payload(document_version=0))
        assert getattr(exc.value, "code", "") == "INVALID_REQUEST"


class TestClaimExtraction:
    def test_segments_answer_into_spans(self, service, analyst):
        text = make_answer_text()
        result = service.invoke("claim_extraction", analyst,
                                {"task_id": TASK_ID, "answer_text": text})
        claims = result.data["claims"]
        assert result.data["claim_count"] == 3
        for claim in claims:
            assert text[claim["span_start"]:claim["span_end"]] == claim["text"]

    def test_spans_are_in_order_and_nonoverlapping(self, service, analyst):
        text = make_answer_text()
        result = service.invoke("claim_extraction", analyst,
                                {"task_id": TASK_ID, "answer_text": text})
        spans = [(c["span_start"], c["span_end"]) for c in result.data["claims"]]
        assert spans == sorted(spans)
        for (_, end1), (start2, _) in zip(spans, spans[1:]):
            assert start2 >= end1

    def test_empty_answer_rejected(self, service, analyst):
        with pytest.raises(Exception) as exc:
            service.invoke("claim_extraction", analyst, {"task_id": TASK_ID, "answer_text": "  "})
        assert getattr(exc.value, "code", "") == "INVALID_REQUEST"

    def test_oversized_answer_rejected(self, service, analyst):
        service.settings.claim_max_chars = 50
        with pytest.raises(Exception) as exc:
            service.invoke("claim_extraction", analyst,
                           {"task_id": TASK_ID, "answer_text": "x" * 51})
        assert getattr(exc.value, "code", "") == "INVALID_REQUEST"

    def test_reextraction_replaces_claims(self, service, analyst):
        payload = {"task_id": TASK_ID, "answer_text": make_answer_text()}
        first = service.invoke("claim_extraction", analyst, payload)
        second = service.invoke("claim_extraction", analyst, payload)
        assert first.data["claim_count"] == 3
        assert second.data["claim_count"] == 3
        # Old claim ids are gone (replaced, not appended).
        old_ids = {c["claim_id"] for c in first.data["claims"]}
        new_ids = {c["claim_id"] for c in second.data["claims"]}
        assert not (old_ids & new_ids)


class TestClaimToSourceMapping:
    def test_link_claim_to_evidence(self, service, analyst):
        service.invoke("claim_extraction", analyst,
                       {"task_id": TASK_ID, "answer_text": make_answer_text()})
        claims = service.claims.claims_for_task(TASK_ID)
        ev = create_evidence(service, analyst)
        result = service.invoke("claim_to_source_mapping", analyst,
                                {"claim_id": claims[0]["claim_id"],
                                 **evidence_payload()})
        assert result.data["claim_id"] == claims[0]["claim_id"]
        # The mapping op creates its own Evidence row and links THAT row.
        new_id = result.data["evidence_id"]
        assert new_id != ev.resource_id
        assert service.claims.evidence_for_claim(claims[0]["claim_id"]) == [new_id]

    def test_unknown_claim_404(self, service, analyst):
        import uuid as _uuid
        with pytest.raises(Exception) as exc:
            service.invoke("claim_to_source_mapping", analyst,
                           {"claim_id": str(_uuid.uuid4()), **evidence_payload()})
        assert getattr(exc.value, "code", "") == "FILE_NOT_FOUND"

    def test_task_mismatch_rejected(self, service, analyst):
        import uuid as _uuid
        other_task = str(_uuid.uuid4())
        service.invoke("claim_extraction", analyst,
                       {"task_id": TASK_ID, "answer_text": make_answer_text()})
        claims = service.claims.claims_for_task(TASK_ID)
        with pytest.raises(Exception) as exc:
            service.invoke("claim_to_source_mapping", analyst,
                           {"claim_id": claims[0]["claim_id"],
                            **evidence_payload(task_id=other_task)})
        assert getattr(exc.value, "code", "") == "INVALID_REQUEST"


class TestCitations:
    def test_page_level_citation(self, service, analyst):
        create_evidence(service, analyst)
        eid = service.links.for_task(TASK_ID)[0].id
        result = service.invoke("page_level_citations", analyst,
                                {"evidence_id": eid})
        assert result.data["page_number"] == 3
        assert result.data["document_version"] == 1

    def test_coordinate_level_citation(self, service, analyst):
        create_evidence(service, analyst)
        eid = service.links.for_task(TASK_ID)[0].id
        result = service.invoke("coordinate_level_citations", analyst,
                                {"evidence_id": eid})
        assert result.data["bbox"] == [72.0, 100.0, 300.0, 140.0]
        assert result.data["page_number"] == 3

    def test_coordinate_citation_requires_bbox(self, service, analyst):
        create_evidence(service, analyst)
        seed_chunk(service)  # reseed without bbox
        service.retrieval.seed_chunk(CHUNK_ID, DOC_ID, chunk_index=0,
                                     page_number=3, bbox=None)
        eid = service.links.for_task(TASK_ID)[0].id
        with pytest.raises(Exception) as exc:
            service.invoke("coordinate_level_citations", analyst, {"evidence_id": eid})
        assert getattr(exc.value, "code", "") == "INVALID_REQUEST"

    def test_page_citation_without_any_page_number(self, service, analyst):
        create_evidence(service, analyst, page_number=None)
        service.retrieval.seed_chunk(CHUNK_ID, DOC_ID, chunk_index=0,
                                     page_number=None, bbox=None)
        eid = service.links.for_task(TASK_ID)[0].id
        with pytest.raises(Exception) as exc:
            service.invoke("page_level_citations", analyst, {"evidence_id": eid})
        assert getattr(exc.value, "code", "") == "INVALID_REQUEST"

    def test_citation_span_rendered_and_validated(self, service, analyst):
        create_evidence(service, analyst)
        eid = service.links.for_task(TASK_ID)[0].id
        result = service.invoke("page_level_citations", analyst,
                                {"evidence_id": eid,
                                 "text_span_start": 4, "text_span_end": 40})
        assert result.data["citation"]["evidence_id"] == eid
        assert service.links.citations_for(eid)[0].text_span_end == 40

    def test_inverted_span_rejected(self, service, analyst):
        create_evidence(service, analyst)
        eid = service.links.for_task(TASK_ID)[0].id
        with pytest.raises(Exception) as exc:
            service.invoke("page_level_citations", analyst,
                           {"evidence_id": eid,
                            "text_span_start": 40, "text_span_end": 4})
        assert getattr(exc.value, "code", "") == "INVALID_REQUEST"

    def test_unknown_evidence_404(self, service, analyst):
        import uuid as _uuid
        with pytest.raises(Exception) as exc:
            service.invoke("page_level_citations", analyst,
                           {"evidence_id": str(_uuid.uuid4())})
        assert getattr(exc.value, "code", "") == "FILE_NOT_FOUND"

    def test_chunk_missing_from_retrieval_view_fails_closed(self, service, analyst):
        # RAG_INDEX_UNAVAILABLE per feature docs §17 — never a silent degraded answer.
        seed_chain(service)
        result = service.invoke("evidence_system", analyst,
                                evidence_payload(chunk_id=str(__import__("uuid").uuid4())))
        eid = result.resource_id
        with pytest.raises(Exception) as exc:
            service.invoke("page_level_citations", analyst, {"evidence_id": eid})
        assert getattr(exc.value, "code", "") == "RAG_INDEX_UNAVAILABLE"


class TestSourceChain:
    def test_single_link_chain(self, service, analyst):
        create_evidence(service, analyst)
        eid = service.links.for_task(TASK_ID)[0].id
        result = service.invoke("source_chain", analyst, {"evidence_id": eid})
        chain = result.data["chain"]
        assert len(chain) == 1
        assert chain[0]["version"] == 1
        assert chain[0]["is_current"] is True
        assert result.data["complete"] is True

    def test_superseded_source_chain_walks_to_current(self, service, analyst):
        v2_doc = "44444444-4444-4444-8444-444444444444"
        seed_chain(service, version=1)
        seed_chain(service, document_id=v2_doc, version=2, authority="primary")
        # v1 is superseded by v2 via explicit pointer.
        service.chains.seed_document(DOC_ID, 1, "a" * 64, "primary",
                                     effective_from=None, effective_until=None)
        service.chains._versions[DOC_ID][0]["superseded_by"] = v2_doc
        create_evidence(service, analyst)  # evidence pinned to v1
        eid = service.links.for_task(TASK_ID)[0].id
        result = service.invoke("source_chain", analyst, {"evidence_id": eid})
        chain = result.data["chain"]
        assert [s["version"] for s in chain] == [1, 2]
        assert chain[0]["is_current"] is False
        assert chain[-1]["is_current"] is True
        assert result.data["complete"] is True

    def test_broken_chain_fails_closed(self, service, analyst):
        # Evidence referencing a document version the chain store doesn't know.
        result = service.invoke("evidence_system", analyst,
                                evidence_payload(document_version=9))
        eid = result.resource_id
        with pytest.raises(Exception) as exc:
            service.invoke("source_chain", analyst, {"evidence_id": eid})
        assert getattr(exc.value, "code", "") == "RAG_INDEX_UNAVAILABLE"

    def test_cyclic_chain_detected(self, service, analyst):
        doc_b = "55555555-5555-4555-8555-555555555555"
        seed_chain(service, version=1)
        seed_chain(service, document_id=doc_b, version=1)
        service.chains._versions[DOC_ID][0]["superseded_by"] = doc_b
        service.chains._versions[doc_b][0]["superseded_by"] = DOC_ID
        create_evidence(service, analyst)
        eid = service.links.for_task(TASK_ID)[0].id
        with pytest.raises(Exception) as exc:
            service.invoke("source_chain", analyst, {"evidence_id": eid})
        assert getattr(exc.value, "code", "") == "RESOURCE_CONFLICT"


class TestEvidenceGraph:
    def test_graph_nodes_and_edges(self, service, analyst):
        service.invoke("claim_extraction", analyst,
                       {"task_id": TASK_ID, "answer_text": make_answer_text()})
        create_evidence(service, analyst)
        ev_id = service.links.for_task(TASK_ID)[0].id
        claim_id = service.claims.claims_for_task(TASK_ID)[0]["claim_id"]
        service.claims.link_claim(claim_id, ev_id)
        result = service.invoke("evidence_graph", analyst, {"task_id": TASK_ID})
        kinds = {n["kind"] for n in result.data["nodes"]}
        assert kinds == {"claim", "evidence"}
        edge_kinds = {e["kind"] for e in result.data["edges"]}
        assert "supported_by" in edge_kinds
        assert "derived_from" in edge_kinds

    def test_shares_source_edges(self, service, analyst):
        create_evidence(service, analyst)
        create_evidence(service, analyst, chunk_id=CHUNK_ID)  # same doc, second row
        rows = service.links.for_task(TASK_ID)
        assert len(rows) == 2
        result = service.invoke("evidence_graph", analyst, {"task_id": TASK_ID})
        assert any(e["kind"] == "shares_source" for e in result.data["edges"])

    def test_empty_task_graph(self, service, analyst):
        result = service.invoke("evidence_graph", analyst, {"task_id": TASK_ID})
        assert result.data["node_count"] == 0
        assert result.data["edge_count"] == 0


class TestConfidence:
    def test_no_single_number_ever_returned(self, service, analyst):
        create_evidence(service, analyst)
        result = service.invoke("confidence", analyst, {"task_id": TASK_ID})
        assert "score" not in result.data
        assert "confidence" not in result.data
        axes = result.data["axes"]
        assert set(axes) == {"evidence_coverage", "evidence_coverage_detail",
                             "source_authority", "freshness",
                             "cross_source_agreement"}

    def test_four_axes_values(self, service, analyst):
        create_evidence(service, analyst)  # primary authority, current, unverified
        result = service.invoke("confidence", analyst, {"task_id": TASK_ID})
        per = result.data["per_evidence"][0]
        assert per["source_authority"] == "Primary"
        assert per["freshness"] == "Current"
        assert per["cross_source_agreement"] == "Unverified"

    def test_raw_confidence_only_as_labeled_debug_signal(self, service, analyst):
        create_evidence(service, analyst)
        result = service.invoke("confidence", analyst, {"task_id": TASK_ID})
        dbg = result.data["raw_confidence_debug"]
        assert "NOT a correctness probability" in dbg["label"]
        assert dbg["values"][0]["confidence"] == 0.83

    def test_coverage_without_claims_is_unknown_not_invented(self, service, analyst):
        create_evidence(service, analyst)
        result = service.invoke("confidence", analyst, {"task_id": TASK_ID})
        assert result.data["axes"]["evidence_coverage"] == "Unknown"

    def test_coverage_low_partial_high(self, service, analyst):
        service.invoke("claim_extraction", analyst,
                       {"task_id": TASK_ID, "answer_text": make_answer_text()})
        claims = service.claims.claims_for_task(TASK_ID)
        ev = create_evidence(service, analyst)
        # 1/3 claims covered -> Low (below 0.5).
        service.claims.link_claim(claims[0]["claim_id"], ev.resource_id)
        low = service.invoke("confidence", analyst, {"task_id": TASK_ID})
        assert low.data["axes"]["evidence_coverage"] == "Low"

    def test_superseded_freshness_axis(self, service, analyst):
        create_evidence(service, analyst)
        # Mark v1 superseded by seeding a v2 after the fact.
        seed_chain(service, version=2, authority="primary")
        result = service.invoke("confidence", analyst, {"task_id": TASK_ID})
        assert result.data["per_evidence"][0]["freshness"] == "Superseded"
