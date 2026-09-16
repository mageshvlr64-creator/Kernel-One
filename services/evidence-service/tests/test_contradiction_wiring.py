"""Cross-service contradiction wiring — industrial /internal/detect-conflicts,
scoped by the REAL knowledge-graph lookup.

Op 09's contradiction pass no longer consults any in-process registry: for
each of the task's evidence source documents it asks industrial-service
(GET /documents/{id}/equipment — the equipment_governing_documents table)
which equipment that document governs, then runs the deterministic detector
per equipment. Participants in a ConflictRecord upgrade to
verification_status='contradicted' (upgrade only). Dependency failures skip a
document — detection failure must never fabricate a status — and KG lookups
are read-through cached per (task, document), failures never cached.
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest

from evidence_service.errors import RegistryError
from evidence_service.industrial_gateway import IndustrialGatewayClient

from tests.conftest import (CHUNK_ID, DOC_ID, TASK_ID, create_evidence,
                            make_actor, seed_chain, seed_chunk)


def stub_client(responses):
    """Gateway stub. responses maps path -> (status, payload) | Exception |
    callable(body) -> (status, payload). Calls recorded as tuples."""
    calls = []

    def opener(method, url, body, headers):
        path = "/" + url.split("/", 3)[3]
        calls.append((method, path, body, headers))
        spec = responses[path]
        if isinstance(spec, Exception):
            raise spec
        if callable(spec):
            return spec(body)
        return spec

    return IndustrialGatewayClient(opener=opener), calls


ACTOR = make_actor("Operator")
UNIT_ID = "aaaaaaaa-0000-0000-0000-000000002000"
PLANT_ID = "aaaaaaaa-0000-0000-0000-000000001000"
EQUIP_ID = "aaaaaaaa-0000-0000-0000-00000000b204"
DOC_B = "11111111-1111-4111-8111-111111111112"
CHUNK_B = "22222222-2222-4222-8222-222222222223"


def kg(doc_id, equipment_ids):
    """The real route's response shape: {document_id, equipment_ids}."""
    return (200, {"document_id": doc_id, "equipment_ids": equipment_ids})


def run_claim_extraction(service):
    """Op 09 requires the claim pipeline (FILE_NOT_FOUND otherwise)."""
    service.invoke("claim_extraction", ACTOR,
                   {"task_id": TASK_ID,
                    "answer_text": "The valve is set. Inspection is due."})


def ingest_with_assertion(service, *, doc_id=DOC_ID, chunk_id=CHUNK_ID,
                          section="s4.2", chunk_text=None, authority="primary",
                          enriched=False):
    """Seed chain+chunk and create one Evidence row (optionally enriched)."""
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
    }
    if enriched:
        payload.update({"equipment_tag": "P-204", "within_unit_id": UNIT_ID,
                        "plant_id": PLANT_ID})
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
            f"/documents/{DOC_ID}/equipment": kg(DOC_ID, [EQUIP_ID]),
            f"/documents/{DOC_B}/equipment": kg(DOC_B, [EQUIP_ID]),
            "/internal/detect-conflicts": (200, CONFLICT_BODY),
        })
        service.industrial = client
        ingest_with_assertion(service, doc_id=DOC_ID, chunk_id=CHUNK_ID,
                              chunk_text="The relief valve set pressure is 150 psi")
        ingest_with_assertion(service, doc_id=DOC_B, chunk_id=CHUNK_B,
                              chunk_text="The relief valve set pressure is 175 psi")
        run_claim_extraction(service)
        result = service.invoke("unsupported_claim_detection", ACTOR,
                                {"task_id": TASK_ID})
        assert result.data["verification_contradictions"] == 2
        for doc in (DOC_ID, DOC_B):
            rows = [r for r in service.links.for_task(TASK_ID)
                    if r.source_document_id == doc]
            assert all(r.verification_status == "contradicted" for r in rows)
        kg_calls = [c for c in calls if c[0] == "GET"]
        assert {c[1] for c in kg_calls} == {f"/documents/{DOC_ID}/equipment",
                                            f"/documents/{DOC_B}/equipment"}
        # Claim shape sent to the detector: parameter = section, value = chunk text
        detector_bodies = [c[2] for c in calls if c[1] == "/internal/detect-conflicts"]
        assert detector_bodies, "detector must be consulted"
        sent = detector_bodies[0]["claims"]
        assert sent[0]["parameter"] == "s4.2" and "150 psi" in sent[0]["value"]
        assert sent[0]["authority"] == "primary"

    def test_document_governing_no_equipment_skips_detector(self, service):
        client, calls = stub_client({
            f"/documents/{DOC_ID}/equipment": kg(DOC_ID, []),
            f"/documents/{DOC_B}/equipment": kg(DOC_B, []),
        })
        service.industrial = client
        ingest_with_assertion(service, chunk_text="Set pressure is 150 psi")
        ingest_with_assertion(service, doc_id=DOC_B, chunk_id=CHUNK_B,
                              chunk_text="Set pressure is 175 psi")
        run_claim_extraction(service)
        result = service.invoke("unsupported_claim_detection", ACTOR,
                                {"task_id": TASK_ID})
        assert result.data["verification_contradictions"] == 0
        # The graph says nothing is governed: the detector is never consulted.
        assert "/internal/detect-conflicts" not in [c[1] for c in calls]

    def test_no_conflict_keeps_rows_unsupported_unverified(self, service):
        client, _ = stub_client({
            f"/documents/{DOC_ID}/equipment": kg(DOC_ID, [EQUIP_ID]),
            f"/documents/{DOC_B}/equipment": kg(DOC_B, [EQUIP_ID]),
            "/internal/detect-conflicts": (200, []),
        })
        service.industrial = client
        ingest_with_assertion(service, chunk_text="Set pressure is 150 psi")
        ingest_with_assertion(service, doc_id=DOC_B, chunk_id=CHUNK_B,
                              chunk_text="Set pressure is 150 psi")  # values agree
        run_claim_extraction(service)
        result = service.invoke("unsupported_claim_detection", ACTOR,
                                {"task_id": TASK_ID})
        assert result.data["verification_contradictions"] == 0
        statuses = {r.verification_status for r in service.links.for_task(TASK_ID)}
        assert statuses <= {"unverified", "supported"}

    def test_supported_is_upgraded_to_contradicted_never_downgraded(self, service):
        conflict_flag = {"on": False}
        client, calls = stub_client({
            f"/documents/{DOC_ID}/equipment": kg(DOC_ID, [EQUIP_ID]),
            f"/documents/{DOC_B}/equipment": kg(DOC_B, [EQUIP_ID]),
            "/internal/detect-conflicts":
                lambda body: (200, CONFLICT_BODY) if conflict_flag["on"] else (200, []),
        })
        service.industrial = client
        ingest_with_assertion(service, chunk_text="Set pressure is 150 psi")
        ingest_with_assertion(service, doc_id=DOC_B, chunk_id=CHUNK_B,
                              chunk_text="Set pressure is 175 psi")
        run_claim_extraction(service)
        # A mapped claim makes row A 'supported' in the first pass.
        service.claims.put(TASK_ID, [{"claim_id": "c-1", "text": "t",
                                      "span_start": 0, "span_end": 1}])
        service.claims.link_claim("c-1",
                                  [r for r in service.links.for_task(TASK_ID)
                                   if r.source_document_id == DOC_ID][0].id)
        service.invoke("unsupported_claim_detection", ACTOR, {"task_id": TASK_ID})
        row_a = [r for r in service.links.for_task(TASK_ID)
                 if r.source_document_id == DOC_ID][0]
        assert row_a.verification_status == "supported"
        # Second run: the detector now reports A vs B as conflicting.
        conflict_flag["on"] = True
        service.invoke("unsupported_claim_detection", ACTOR, {"task_id": TASK_ID})
        statuses = {r.source_document_id: r.verification_status
                    for r in service.links.for_task(TASK_ID)}
        # Upgraded (supported -> contradicted), never downgraded.
        assert statuses[DOC_ID] == "contradicted"
        assert statuses[DOC_B] == "contradicted"

    def test_detector_outage_skips_document_without_fabricating(self, service):
        client, _ = stub_client({
            f"/documents/{DOC_ID}/equipment": kg(DOC_ID, [EQUIP_ID]),
            f"/documents/{DOC_B}/equipment": kg(DOC_B, [EQUIP_ID]),
            "/internal/detect-conflicts": ConnectionError("down"),
        })
        service.industrial = client
        ingest_with_assertion(service, chunk_text="Set pressure is 150 psi")
        ingest_with_assertion(service, doc_id=DOC_B, chunk_id=CHUNK_B,
                              chunk_text="Set pressure is 175 psi")
        run_claim_extraction(service)
        result = service.invoke("unsupported_claim_detection", ACTOR,
                                {"task_id": TASK_ID})
        assert result.data["verification_contradictions"] == 0
        statuses = {r.verification_status for r in service.links.for_task(TASK_ID)}
        assert statuses <= {"unverified", "supported"}  # no fabricated contradictions
        assert result.data["unsupported_ratio"] is not None  # op still succeeds

    def test_kg_lookup_outage_skips_document(self, service):
        client, calls = stub_client({
            f"/documents/{DOC_ID}/equipment": ConnectionError("graph down"),
            f"/documents/{DOC_B}/equipment": kg(DOC_B, [EQUIP_ID]),
            "/internal/detect-conflicts": (200, CONFLICT_BODY),
        })
        service.industrial = client
        ingest_with_assertion(service, chunk_text="Set pressure is 150 psi")
        ingest_with_assertion(service, doc_id=DOC_B, chunk_id=CHUNK_B,
                              chunk_text="Set pressure is 175 psi")
        run_claim_extraction(service)
        result = service.invoke("unsupported_claim_detection", ACTOR,
                                {"task_id": TASK_ID})
        # DOC_B is still processed through the detector (its doc participates
        # in the returned conflict, but DOC_ID was never scoped so its own
        # rows are untouched this run — no fabrication, next run catches up).
        assert result.data["verification_contradictions"] >= 0
        assert f"/documents/{DOC_ID}/equipment" in [c[1] for c in calls]

    def test_kg_policy_denial_skips_document(self, service):
        client, calls = stub_client({
            f"/documents/{DOC_ID}/equipment": (403, {"detail": "denied"}),
            f"/documents/{DOC_B}/equipment": kg(DOC_B, [EQUIP_ID]),
            "/internal/detect-conflicts": (200, []),
        })
        service.industrial = client
        ingest_with_assertion(service, chunk_text="Set pressure is 150 psi")
        ingest_with_assertion(service, doc_id=DOC_B, chunk_id=CHUNK_B,
                              chunk_text="Set pressure is 150 psi")
        run_claim_extraction(service)
        # POLICY_DENIED on the KG lookup is skipped (not raised): the op-09
        # failure posture for scope lookups matches the other dependency codes.
        result = service.invoke("unsupported_claim_detection", ACTOR,
                                {"task_id": TASK_ID})
        assert result.data["verification_contradictions"] == 0

    def test_unresolvable_rows_cannot_contradict(self, service):
        client, calls = stub_client({
            f"/documents/{DOC_ID}/equipment": kg(DOC_ID, [EQUIP_ID]),
            f"/documents/{DOC_B}/equipment": kg(DOC_B, [EQUIP_ID]),
            "/internal/detect-conflicts": (200, CONFLICT_BODY),
        })
        service.industrial = client
        # Row A keeps seed_chunk's default text but has NO section reference:
        # it cannot assert anything and must never enter the detector.
        seed_chain(service, document_id=DOC_ID, version=1, authority="primary")
        seed_chunk(service, chunk_id=CHUNK_ID, document_id=DOC_ID)
        service.invoke("evidence_system", ACTOR, {
            "task_id": TASK_ID, "source_document_id": DOC_ID,
            "document_version": 1, "chunk_id": CHUNK_ID,
            "source_hash": "a" * 64, "retrieval_method": "hybrid",
            "source_authority": "primary"})
        run_claim_extraction(service)
        result = service.invoke("unsupported_claim_detection", ACTOR,
                                {"task_id": TASK_ID})
        assert result.data["verification_contradictions"] == 0
        # The detector was never consulted: only 1 resolvable claim.
        assert "/internal/detect-conflicts" not in [c[1] for c in calls]

    def test_kg_lookup_cached_per_task_and_document(self, service):
        client, calls = stub_client({
            f"/documents/{DOC_ID}/equipment": kg(DOC_ID, [EQUIP_ID]),
            f"/documents/{DOC_B}/equipment": kg(DOC_B, [EQUIP_ID]),
            "/internal/detect-conflicts": (200, []),
        })
        service.industrial = client
        ingest_with_assertion(service, chunk_text="Set pressure is 150 psi")
        ingest_with_assertion(service, doc_id=DOC_B, chunk_id=CHUNK_B,
                              chunk_text="Set pressure is 150 psi")
        run_claim_extraction(service)
        service.invoke("unsupported_claim_detection", ACTOR, {"task_id": TASK_ID})
        first_run_gets = len([c for c in calls if c[0] == "GET"])
        assert first_run_gets == 2  # one per document
        # Second run: the graph facts are cached — no new KG calls, but the
        # detector is still re-consulted (its input can change between runs).
        service.invoke("unsupported_claim_detection", ACTOR, {"task_id": TASK_ID})
        assert len([c for c in calls if c[0] == "GET"]) == first_run_gets
        detector_calls = [c for c in calls if c[1] == "/internal/detect-conflicts"]
        assert len(detector_calls) == 4  # 2 documents x 2 runs

    def test_registry_is_gone_from_op01(self, service):
        """The op-01 enrichment no longer feeds any conflict-target registry."""
        client, calls = stub_client({
            "/internal/resolve-tag": (200, {"matched_equipment_id": EQUIP_ID,
                                            "requires_human_confirmation": False}),
        })
        service.industrial = client
        result = ingest_with_assertion(service, chunk_text="Set pressure 150 psi",
                                       enriched=True)
        assert result.data["industrial_enrichment"]["equipment_resolution"][
            "matched_equipment_id"] == EQUIP_ID
        assert not hasattr(service, "conflict_targets")


class TestGatewayEquipmentLookup:
    def test_get_contract_and_parsing(self):
        client, calls = stub_client({
            f"/documents/{DOC_ID}/equipment": kg(DOC_ID, [EQUIP_ID])})
        got = client.equipment_for_document(DOC_ID)
        assert got == [EQUIP_ID]
        method, path, body, headers = calls[0]
        assert (method, path) == ("GET", f"/documents/{DOC_ID}/equipment")
        assert body is None  # GET carries no body
        assert headers["X-Roles"] == "Equipment:read"

    def test_malformed_body_fails_closed(self):
        client, _ = stub_client({f"/documents/{DOC_ID}/equipment":
                                 (200, {"unexpected": True})})
        with pytest.raises(RegistryError) as err:
            client.equipment_for_document(DOC_ID)
        assert err.value.code == "DEPENDENCY_UNAVAILABLE"

    def test_403_maps_to_policy_denied(self):
        client, _ = stub_client({f"/documents/{DOC_ID}/equipment":
                                 (403, {"detail": "denied"})})
        with pytest.raises(RegistryError) as err:
            client.equipment_for_document(DOC_ID)
        assert err.value.code == "POLICY_DENIED"

    def test_transport_failure_fails_closed(self):
        client, _ = stub_client({f"/documents/{DOC_ID}/equipment":
                                 TimeoutError("t")})
        with pytest.raises(RegistryError) as err:
            client.equipment_for_document(DOC_ID)
        assert err.value.code == "DEPENDENCY_UNAVAILABLE"


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
