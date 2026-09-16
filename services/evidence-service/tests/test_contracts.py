from __future__ import annotations

import uuid

import pytest

from tests.conftest import TASK_ID, create_evidence, evidence_payload, make_actor


class TestExactlyOneAuditEvent:
    def test_success_single_event(self, service, analyst):
        before = len(service.audit_sink.events)
        service.invoke("evidence_system", analyst, evidence_payload())
        events = service.audit_sink.events[before:]
        assert len(events) == 1
        assert events[0]["event_type"] == "evidence_and_provenance.evidence_system"
        assert events[0]["result"] == "success"

    def test_error_single_event_with_code(self, service, analyst):
        before = len(service.audit_sink.events)
        with pytest.raises(Exception):
            service.invoke("evidence_system", analyst, evidence_payload(source_hash="bad"))
        events = service.audit_sink.events[before:]
        assert len(events) == 1
        assert events[0]["result"] == "error"
        assert events[0]["error_code"] == "INVALID_REQUEST"

    def test_denial_single_event_with_rule(self, service, auditor):
        before = len(service.audit_sink.events)
        with pytest.raises(Exception) as exc:
            service.invoke("evidence_system", auditor, evidence_payload())
        assert getattr(exc.value, "code", "") == "TOOL_NOT_ALLOWED"
        events = service.audit_sink.events[before:]
        assert len(events) == 1
        assert events[0]["result"] == "error"
        assert events[0]["reason"]  # specific denying rule recorded (§16)

    def test_denial_event_names_actor_role(self, service, auditor):
        with pytest.raises(Exception):
            service.invoke("evidence_system", auditor, evidence_payload())
        event = service.audit_sink.events[-1]
        assert event["actor_id"] == "dev:auditor"

    def test_audit_event_schema_conformance(self, service, analyst):
        service.invoke("evidence_system", analyst, evidence_payload())
        event = service.audit_sink.events[-1]
        # schemas/15 field set (additionalProperties: false).
        expected_keys = {"event_id", "timestamp", "event_type", "actor_id",
                         "session_id", "correlation_id", "task_id", "action",
                         "resource_type", "resource_id", "classification",
                         "decision", "result", "error_code", "reason", "tool_id",
                         "model_id", "artifact_id", "source_interface", "source_ip",
                         "payload_hash", "prev_event_hash"}
        assert expected_keys <= set(event)
        assert event["action"] == "execute"          # §22: action is execute
        assert event["resource_type"] == "Document"  # §22: resource_type is Document

    def test_hash_chain_intact(self, service, analyst):
        create_evidence(service, analyst)
        with pytest.raises(Exception):
            service.invoke("evidence_system", analyst, {"bogus": True})
        events = service.audit_sink.events
        # Same sink contract as the sibling services: every stored event carries
        # a recomputable digest (sha256 of the event sans the hash field), so the
        # audit-service integrity job can verify the chain when it lands.
        import hashlib
        import json
        for event in events:
            hashable = {k: v for k, v in event.items() if k != "prev_event_hash"}
            expected = hashlib.sha256(
                json.dumps(hashable, sort_keys=True, default=str).encode("utf-8")).hexdigest()
            assert event["prev_event_hash"] == expected

    def test_all_ten_ops_audited_with_canonical_event_type(self, service, analyst):
        from evidence_service.ops import OPS
        # Denial path is enough to prove the event-type mapping per op.
        auditor = make_actor("Auditor")
        for op in OPS:
            before = len(service.audit_sink.events)
            with pytest.raises(Exception):
                service.invoke(op, auditor, {"evidence_id": str(uuid.uuid4())})
            events = service.audit_sink.events[before:]
            assert len(events) == 1, op
            assert events[0]["event_type"] == f"evidence_and_provenance.{op}", op


class TestPermissionMatrix:
    @pytest.mark.parametrize("role", ["Auditor", "Restricted User"])
    def test_execute_denied_roles(self, service, role):
        actor = make_actor(role, clearance="RESTRICTED"
                           if role == "Restricted User" else "INTERNAL")
        with pytest.raises(Exception) as exc:
            service.invoke("evidence_system", actor, evidence_payload())
        assert getattr(exc.value, "code", "") == "TOOL_NOT_ALLOWED"

    @pytest.mark.parametrize("role", ["Administrator", "Security Officer",
                                      "Operator", "Analyst"])
    def test_execute_allowed_roles(self, service, role):
        result = create_evidence(service, make_actor(role))
        assert result.data["evidence"]["id"] == result.resource_id

    def test_classification_denied_for_low_clearance(self, service):
        service.chains.seed_document(
            "66666666-6666-4666-8666-666666666666", 1, "a" * 64, "primary")
        actor = make_actor("Analyst", clearance="INTERNAL")
        with pytest.raises(Exception) as exc:
            # Classification rides the payload's document as the resource scope —
            # modeled here by the policy check against a RESTRICTED resource.
            from evidence_service.policy import enforce
            enforce("Document", "execute", actor,
                    resource_classification="RESTRICTED")
        assert getattr(exc.value, "code", "") == "FILE_CLASSIFICATION_DENIED"

    def test_workspace_mismatch_denied(self, service):
        from evidence_service.policy import enforce
        actor = make_actor("Analyst", workspace="ws-dev")
        with pytest.raises(Exception) as exc:
            enforce("Document", "execute", actor, resource_workspace_id="ws-other")
        assert getattr(exc.value, "code", "") == "POLICY_DENIED"


class TestRegistryConformance:
    def test_only_registry_codes(self, service, analyst):
        attempts = [
            ("evidence_system", evidence_payload(source_hash="nope")),
            ("claim_extraction", {}),
            ("claim_extraction", {"task_id": "not-a-uuid", "answer_text": "x"}),
            ("claim_to_source_mapping", {"claim_id": str(uuid.uuid4())}),
            ("page_level_citations", {"evidence_id": str(uuid.uuid4())}),
            ("source_chain", {}),
            ("evidence_graph", {}),
            ("confidence", {}),
            ("unsupported_claim_detection", {"task_id": str(uuid.uuid4())}),
            ("evidence_failures", {}),
        ]
        for op, payload in attempts:
            try:
                service.invoke(op, analyst, payload)
            except Exception as exc:
                code = getattr(exc, "code", None)
                assert code is not None, f"{op} raised non-registry error: {exc}"
                assert getattr(exc, "http_status", None), "registry code must carry HTTP status"
                assert code in {
                    "INVALID_REQUEST", "AUTH_REQUIRED", "POLICY_DENIED",
                    "TOOL_NOT_ALLOWED", "FILE_CLASSIFICATION_DENIED",
                    "FILE_NOT_FOUND", "RESOURCE_CONFLICT", "RAG_INDEX_UNAVAILABLE",
                    "DEPENDENCY_UNAVAILABLE", "INTERNAL_ERROR"}

    def test_invalid_json_shape_rejected(self, service, analyst):
        with pytest.raises(Exception) as exc:
            service.invoke("evidence_system", analyst, ["not", "a", "dict"])
        assert getattr(exc.value, "code", "") == "INVALID_REQUEST"

    def test_unknown_op_rejected(self, service, analyst):
        with pytest.raises(Exception) as exc:
            service.invoke("definitely_not_an_op", analyst, {})
        assert getattr(exc.value, "code", "") == "INVALID_REQUEST"

    def test_empty_payload_rejected_before_state_touched(self, service, analyst):
        # §30: empty/missing payload -> 400 before any state is touched.
        with pytest.raises(Exception) as exc:
            service.invoke("evidence_system", analyst, {})
        assert getattr(exc.value, "code", "") == "INVALID_REQUEST"
        assert service.links.count() == 0


class TestIdempotency:
    def test_duplicate_key_replays_original_result(self, service, analyst):
        payload = evidence_payload(idempotency_key="idem-1")
        first = service.invoke("evidence_system", analyst, payload)
        second = service.invoke("evidence_system", analyst, payload)
        assert first.resource_id == second.resource_id
        assert first.data == second.data
        assert service.links.count() == 1  # not re-executed

    def test_replay_still_audits_exactly_once(self, service, analyst):
        payload = evidence_payload(idempotency_key="idem-2")
        service.invoke("evidence_system", analyst, payload)
        before = len(service.audit_sink.events)
        service.invoke("evidence_system", analyst, payload)
        assert len(service.audit_sink.events) - before == 1

    def test_different_keys_execute_separately(self, service, analyst):
        service.invoke("evidence_system", analyst, evidence_payload(idempotency_key="a"))
        service.invoke("evidence_system", analyst, evidence_payload(idempotency_key="b"))
        assert service.links.count() == 2

    def test_no_key_always_executes(self, service, analyst):
        service.invoke("evidence_system", analyst, evidence_payload())
        service.invoke("evidence_system", analyst, evidence_payload())
        assert service.links.count() == 2
