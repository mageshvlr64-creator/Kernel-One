from __future__ import annotations

import uuid

import pytest

from tests.conftest import (CHUNK_ID, DOC_ID, TASK_ID, create_evidence,
                            evidence_payload, make_answer_text, seed_chain,
                            seed_chunk)


class TestUnsupportedClaimDetection:
    def _extract(self, service, analyst):
        service.invoke("claim_extraction", analyst,
                       {"task_id": TASK_ID, "answer_text": make_answer_text()})
        return service.claims.claims_for_task(TASK_ID)

    def test_unsupported_claim_flagged(self, service, analyst):
        claims = self._extract(service, analyst)
        ev = create_evidence(service, analyst)
        service.claims.link_claim(claims[0]["claim_id"], ev.resource_id)
        result = service.invoke("unsupported_claim_detection", analyst,
                                {"task_id": TASK_ID})
        assert result.data["total_claims"] == 3
        assert result.data["supported_claim_count"] == 1
        assert result.data["unsupported_claim_count"] == 2
        assert result.data["flagged"] is True  # 2/3 >= 0.2 default
        ids = {c["claim_id"] for c in result.data["unsupported_claims"]}
        assert claims[1]["claim_id"] in ids

    def test_all_supported_not_flagged(self, service, analyst):
        claims = self._extract(service, analyst)
        ev = create_evidence(service, analyst)
        for claim in claims:
            service.claims.link_claim(claim["claim_id"], ev.resource_id)
        result = service.invoke("unsupported_claim_detection", analyst,
                                {"task_id": TASK_ID})
        assert result.data["unsupported_claim_count"] == 0
        assert result.data["flagged"] is False

    def test_no_claims_is_file_not_found(self, service, analyst):
        with pytest.raises(Exception) as exc:
            service.invoke("unsupported_claim_detection", analyst, {"task_id": TASK_ID})
        assert getattr(exc.value, "code", "") == "FILE_NOT_FOUND"

    def test_never_downgrades_contradicted(self, service, analyst):
        # domain/13: contradicted is conflict detection's (industrial/14) output —
        # op 09 must never overwrite it, even for fully supported claims.
        claims = self._extract(service, analyst)
        ev = create_evidence(service, analyst)
        service.links.set_verification_status(ev.resource_id, "contradicted")
        for claim in claims:
            service.claims.link_claim(claim["claim_id"], ev.resource_id)
        result = service.invoke("unsupported_claim_detection", analyst,
                                {"task_id": TASK_ID})
        assert result.data["unsupported_claim_count"] == 0
        assert service.links.get(ev.resource_id).verification_status == "contradicted"
        assert result.data["verification_status_updates"] == 0

    def test_sets_unverified_rows_to_supported(self, service, analyst):
        claims = self._extract(service, analyst)
        ev = create_evidence(service, analyst)
        service.claims.link_claim(claims[0]["claim_id"], ev.resource_id)
        result = service.invoke("unsupported_claim_detection", analyst,
                                {"task_id": TASK_ID})
        assert result.data["verification_status_updates"] == 1
        assert service.links.get(ev.resource_id).verification_status == "supported"

    def test_threshold_is_configurable(self, service, analyst):
        claims = self._extract(service, analyst)
        ev = create_evidence(service, analyst)
        service.claims.link_claim(claims[0]["claim_id"], ev.resource_id)
        service.settings.unsupported_flag_ratio = 0.9
        result = service.invoke("unsupported_claim_detection", analyst,
                                {"task_id": TASK_ID})
        assert result.data["flagged"] is False  # 2/3 < 0.9


class TestEvidenceFailures:
    def test_healthy_evidence_reports_only_verification_pending(self, service, analyst):
        # A freshly created, unverified row is working as designed — op 09 simply
        # hasn't run yet; that's a status, not a defect.
        create_evidence(service, analyst)
        eid = service.links.for_task(TASK_ID)[0].id
        result = service.invoke("evidence_failures", analyst, {"evidence_id": eid})
        assert result.data["diagnosis"] == [
            {"evidence_id": eid, "issue": "verification_pending",
             "detail": "unsupported-claim detection has not run"}]

    def test_broken_chain_diagnosed(self, service, analyst):
        result = service.invoke("evidence_system", analyst,
                                evidence_payload(document_version=9))
        eid = result.resource_id
        assert eid and eid != TASK_ID  # resource_id is the evidence row
        result = service.invoke("evidence_failures", analyst, {"evidence_id": eid})
        issues = {d["issue"] for d in result.data["diagnosis"]}
        assert "source_chain_broken" in issues

    def test_superseded_source_diagnosed(self, service, analyst):
        create_evidence(service, analyst)
        seed_chain(service, version=2, authority="primary")
        eid = service.links.for_task(TASK_ID)[0].id
        result = service.invoke("evidence_failures", analyst, {"evidence_id": eid})
        issues = {d["issue"] for d in result.data["diagnosis"]}
        assert "source_superseded" in issues

    def test_missing_coordinates_diagnosed(self, service, analyst):
        create_evidence(service, analyst)
        service.retrieval.seed_chunk(CHUNK_ID, DOC_ID, chunk_index=0,
                                     page_number=3, bbox=None)
        eid = service.links.for_task(TASK_ID)[0].id
        result = service.invoke("evidence_failures", analyst, {"evidence_id": eid})
        issues = {d["issue"] for d in result.data["diagnosis"]}
        assert "no_coordinates" in issues
        assert "verification_pending" in issues

    def test_missing_page_diagnosed(self, service, analyst):
        create_evidence(service, analyst, page_number=None)
        service.retrieval.seed_chunk(CHUNK_ID, DOC_ID, chunk_index=0,
                                     page_number=None)
        eid = service.links.for_task(TASK_ID)[0].id
        result = service.invoke("evidence_failures", analyst, {"evidence_id": eid})
        issues = {d["issue"] for d in result.data["diagnosis"]}
        assert "no_page_number" in issues

    def test_task_scoped_diagnosis(self, service, analyst):
        create_evidence(service, analyst)
        result = service.invoke("evidence_failures", analyst, {"task_id": TASK_ID})
        assert result.data["evidence_count"] == 1

    def test_requires_a_scope(self, service, analyst):
        with pytest.raises(Exception) as exc:
            service.invoke("evidence_failures", analyst, {})
        assert getattr(exc.value, "code", "") == "INVALID_REQUEST"
