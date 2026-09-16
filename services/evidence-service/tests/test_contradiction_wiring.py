"""Cross-service contradiction wiring — industrial /internal/detect-conflicts.

Covers the second half of the industrial/14 case-2 flow: op 01 records which
equipment a task's evidence resolved against; op 09 runs the deterministic
detector and upgrades participating Evidence rows to 'contradicted' (upgrade
only — 'supported' and 'contradicted' are never downgraded). Also covers the
op-01 `conflict_check` pass-through enrichment and the industrial-side
ISO-string date normalization the HTTP boundary needs.
"""
from __future__ import annotations

import uuid

import pytest

from evidence_service.errors import RegistryError
from evidence_service.industrial_gateway import IndustrialGatewayClient

from tests.conftest import (CHUNK_ID, DOC_ID, TASK_ID, create_evidence,
                            make_actor, seed_chain, seed_chunk)


def run_claim_extraction(service):
    """Op 09 requires the claim pipeline (FILE_NOT_FOUND otherwise)."""
    service.invoke("claim_extraction", ACTOR,
                   {"task_id": TASK_ID, "answer_text": "The valve is set. "
                                                        "Inspection is due."})


def stub_client(responses):
    calls = []

    def opener(method, url, body, headers):
        path = "/" + url.split("/", 3)[3]
        calls.append((method, path, body, headers))
        spec = responses[path]
        if isinstance(spec, Exception):
            raise spec
        return spec

    return IndustrialGatewayClient(opener=opener), calls


ACTOR = make_actor("Operator")
UNIT_ID = "aaaaaaaa-0000-0000-0000-000000002000"
PLANT_ID = "aaaaaaaa-0000-0000-0000-000000001000"
EQUIP_ID = "aaaaaaaa-0000-0000-0000-00000000b204"
DOC_B = "11111111-1111-4111-8111-111111111112"
CHUNK_B = "22222222-2222-4222-8222-222222222223"


def ingest_for_equipment(service, *, doc_id=DOC_ID, chunk_id=CHUNK_ID,
                         section="s4.2", chunk_text=None, authority="primary"):
    """Seed chain+chunk and ingest one evidence row resolved to EQUIP_ID."""
    seed_chain(service, document_id=doc_id, version=1, authority=authority)
    seed_chunk(service, chunk_id=chunk_id, document_id=doc_id)
    if chunk_text is not None:
        service.retrieval.seed_chunk(chunk_id, doc_id, chunk_index=0,
                                     page_number=3, bbox=[1.0, 2.0, 3.0, 4.0],
                                     text=chunk_text)
    payload = {
        "task_id": TASK_ID, "source_document_id": doc_id,
        "document_version": 1, "chunk_id": chunk_id,
        "source_hash": "a" * 64, "retrieval_method": "hybrid",
        "source_authority": authority, "section_reference": section,
        "equipment_tag": "P-204", "within_unit_id": UNIT_ID,
        "plant_id": PLANT_ID,
    }
    return service.invoke("evidence_system", ACTOR, payload)


CONFLICT_BODY = [{
    "equipment_id": EQUIP_ID,
    "claim_description": "Set pressure for Equipment",
    "source_a_document_id": DOC_ID,
    "source_a_document_name": "document A",
    "source_a_authority": "primary",
    "source_a_effective_from": "2024-01-01",
    "source_a_effective_until": None,
    "source_a_claim": "The relief valve set pressure is 150 psi",
    "source_b_document_id": DOC_B,
    "source_b_document_name": "document B",
    "source_b_authority": "primary",
    "source_b_effective_from": "2024-01-01",
    "source_b_effective_until": None,
    "source_b_claim": "The relief valve set pressure is 175 psi",
    "status": "unresolved",
    "resolution_note": None,
}]


class TestOp09ContradictionPass:
    def test_conflicting_rows_become_contradicted(self, service):
        client, calls = stub_client({
            "/internal/resolve-tag": (200, {"matched_equipment_id": EQUIP_ID,
                                            "requires_human_confirmation": False}),
            "/internal/detect-conflicts": (200, CONFLICT_BODY),
        })
        service.industrial = client
        ingest_for_equipment(service, doc_id=DOC_ID, chunk_id=CHUNK_ID,
                             chunk_text="The relief valve set pressure is 150 psi")
        ingest_for_equipment(service, doc_id=DOC_B, chunk_id=CHUNK_B,
                             chunk_text="The relief valve set pressure is 175 psi")
        run_claim_extraction(service)
        result = service.invoke("unsupported_claim_detection", ACTOR,
                                {"task_id": TASK_ID})
        assert result.data["verification_contradictions"] == 2
        for doc in (DOC_ID, DOC_B):
            rows = [r for r in service.links.for_task(TASK_ID)
                    if r.source_document_id == doc]
            assert all(r.verification_status == "contradicted" for r in rows)
        assert calls[-1][1] == "/internal/detect-conflicts"
        # Claim shape sent to the detector: parameter = section, value = chunk text
        sent = calls[-1][2]["claims"]
        assert sent[0]["parameter"] == "s4.2" and "150 psi" in sent[0]["value"]
        assert sent[0]["authority"] == "primary"

    def test_no_conflict_keeps_rows_unsupported_unverified(self, service):
        client, _ = stub_client({
            "/internal/resolve-tag": (200, {"matched_equipment_id": EQUIP_ID,
                                            "requires_human_confirmation": False}),
            "/internal/detect-conflicts": (200, []),
        })
        service.industrial = client
        ingest_for_equipment(service, chunk_text="Set pressure is 150 psi")
        ingest_for_equipment(service, doc_id=DOC_B, chunk_id=CHUNK_B,
                             chunk_text="Set pressure is 150 psi")  # values agree
        run_claim_extraction(service)
        result = service.invoke("unsupported_claim_detection", ACTOR,
                                {"task_id": TASK_ID})
        assert result.data["verification_contradictions"] == 0
        statuses = {r.verification_status for r in service.links.for_task(TASK_ID)}
        assert statuses <= {"unverified", "supported"}

    def test_supported_is_never_downgraded(self, service):
        client, _ = stub_client({
            "/internal/resolve-tag": (200, {"matched_equipment_id": EQUIP_ID,
                                            "requires_human_confirmation": False}),
            "/internal/detect-conflicts": (200, []),
        })
        service.industrial = client
        ingest_for_equipment(service, chunk_text="Set pressure is 150 psi")
        ingest_for_equipment(service, doc_id=DOC_B, chunk_id=CHUNK_B,
                             chunk_text="Set pressure is 175 psi")
        run_claim_extraction(service)
        # A mapped claim makes row A 'supported' in the first pass.
        service.claims.put(TASK_ID, [{"claim_id": "c-1", "text": "t",
                                      "span_start": 0, "span_end": 1}])
        service.claims.link_claim("c-1", service.links.for_task(TASK_ID)[0].id)
        service.invoke("unsupported_claim_detection", ACTOR, {"task_id": TASK_ID})
        row_a = [r for r in service.links.for_task(TASK_ID)
                 if r.source_document_id == DOC_ID][0]
        assert row_a.verification_status == "supported"
        # Second run: the detector now reports A vs B as conflicting.
        client2, _ = stub_client({"/internal/detect-conflicts": (200, CONFLICT_BODY)})
        service.industrial = client2
        service.invoke("unsupported_claim_detection", ACTOR, {"task_id": TASK_ID})
        statuses = {r.source_document_id: r.verification_status
                    for r in service.links.for_task(TASK_ID)}
        # Upgraded (supported -> contradicted), never downgraded.
        assert statuses[DOC_ID] == "contradicted"
        assert statuses[DOC_B] == "contradicted"

    def test_detector_down_skips_pass_without_fabricating_status(self, service):
        client, _ = stub_client({
            "/internal/resolve-tag": (200, {"matched_equipment_id": EQUIP_ID,
                                            "requires_human_confirmation": False}),
            "/internal/detect-conflicts": ConnectionError("down"),
        })
        service.industrial = client
        ingest_for_equipment(service, chunk_text="Set pressure is 150 psi")
        ingest_for_equipment(service, doc_id=DOC_B, chunk_id=CHUNK_B,
                             chunk_text="Set pressure is 175 psi")
        run_claim_extraction(service)
        result = service.invoke("unsupported_claim_detection", ACTOR,
                                {"task_id": TASK_ID})
        assert result.data["verification_contradictions"] == 0
        statuses = {r.verification_status for r in service.links.for_task(TASK_ID)}
        assert statuses <= {"unverified", "supported"}  # no fabricated contradictions
        # The op itself still succeeds.
        assert result.data["unsupported_ratio"] is not None

    def test_unresolvable_rows_cannot_contradict(self, service):
        client, calls = stub_client({
            "/internal/resolve-tag": (200, {"matched_equipment_id": EQUIP_ID,
                                            "requires_human_confirmation": False}),
            "/internal/detect-conflicts": (200, CONFLICT_BODY),
        })
        service.industrial = client
        # Row A keeps seed_chunk's default text, but has NO section reference:
        # it cannot assert anything and must never enter the detector.
        seed_chain(service, document_id=DOC_ID, version=1, authority="primary")
        seed_chunk(service, chunk_id=CHUNK_ID, document_id=DOC_ID)
        service.invoke("evidence_system", ACTOR, {
            "task_id": TASK_ID, "source_document_id": DOC_ID,
            "document_version": 1, "chunk_id": CHUNK_ID,
            "source_hash": "a" * 64, "retrieval_method": "hybrid",
            "source_authority": "primary",
            "equipment_tag": "P-204", "within_unit_id": UNIT_ID,
            "plant_id": PLANT_ID})
        run_claim_extraction(service)
        result = service.invoke("unsupported_claim_detection", ACTOR,
                                {"task_id": TASK_ID})
        assert result.data["verification_contradictions"] == 0
        # The detector was never consulted: <2 resolvable claims.
        assert "/internal/detect-conflicts" not in [c[1] for c in calls]

    def test_no_conflict_targets_means_no_call(self, service):
        calls = []

        def opener(method, url, body, headers):  # pragma: no cover
            calls.append(url)
            raise AssertionError("detector must not be called")

        service.industrial = IndustrialGatewayClient(opener=opener)
        create_evidence(service, ACTOR)  # plain ingest: no equipment resolution
        run_claim_extraction(service)
        result = service.invoke("unsupported_claim_detection", ACTOR,
                                {"task_id": TASK_ID})
        assert result.data["verification_contradictions"] == 0
        assert calls == []


class TestOp01ConflictCheckEnrichment:
    def test_conflict_check_pass_through(self, service):
        client, calls = stub_client({"/internal/detect-conflicts": (200, [])})
        service.industrial = client
        result = create_evidence(service, ACTOR, conflict_check={
            "equipment_id": EQUIP_ID, "claims": [
                {"document_id": DOC_ID, "authority": "primary",
                 "parameter": "s4.2", "value": "150 psi"}]})
        assert result.data["industrial_enrichment"]["conflicts"] == []
        assert calls[0][1] == "/internal/detect-conflicts"

    def test_conflict_check_validated_before_call(self, service):
        client, calls = stub_client({"/internal/detect-conflicts": (200, [])})
        service.industrial = client
        with pytest.raises(RegistryError) as err:
            create_evidence(service, ACTOR, conflict_check={"equipment_id": "nope"})
        assert err.value.code == "INVALID_REQUEST"
        assert calls == []


class TestIndustrialDateNormalization:
    def test_iso_date_strings_accepted(self):
        """HTTP interop: claims arrive with ISO strings; detector must not 500."""
        import sys
        from pathlib import Path
        root = Path(__file__).resolve().parents[2] / "industrial-service"
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from app.conflict_detection import detect_conflicts as dc

        claims = [
            {"document_id": DOC_ID, "document_name": "A", "authority": "primary",
             "effective_from": "2024-01-01", "effective_until": None,
             "parameter": "s4.2", "value": "150 psi"},
            {"document_id": DOC_B, "document_name": "B", "authority": "primary",
             "effective_from": "2024-01-01T00:00:00Z", "effective_until": None,
             "parameter": "s4.2", "value": "175 psi"},
        ]
        records = dc(uuid.UUID(EQUIP_ID), claims)
        assert len(records) == 1
        assert records[0].status == "unresolved"
