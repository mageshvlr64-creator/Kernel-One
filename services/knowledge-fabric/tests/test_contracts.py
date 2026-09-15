from __future__ import annotations

import pytest

from tests.conftest import make_actor, make_document


class TestExactlyOneAuditEvent:
    def test_success_single_event(self, service, analyst):
        ref = make_document(service)
        before = len(service.audit_sink.events)
        service.invoke("chunking", analyst, {"document_id": ref.document_id})
        events = service.audit_sink.events[before:]
        assert len(events) == 1
        assert events[0]["event_type"] == "knowledge_fabric.chunking"
        assert events[0]["result"] == "success"

    def test_error_single_event_with_code(self, service, analyst):
        before = len(service.audit_sink.events)
        with pytest.raises(Exception):
            service.invoke("chunking", analyst, {"document_id": "missing"})
        events = service.audit_sink.events[before:]
        assert len(events) == 1
        assert events[0]["result"] == "error"
        assert events[0]["error_code"] == "FILE_NOT_FOUND"

    def test_denial_single_event(self, service, auditor):
        ref = make_document(service)
        before = len(service.audit_sink.events)
        with pytest.raises(Exception) as exc:
            service.invoke("chunking", auditor, {"document_id": ref.document_id})
        assert getattr(exc.value, "code", "") == "TOOL_NOT_ALLOWED"
        events = service.audit_sink.events[before:]
        assert len(events) == 1
        assert events[0]["result"] == "error"
        assert events[0]["reason"]  # specific denying rule recorded (§16)

    def test_state_transition_event_only_for_ready(self, service, analyst):
        ref = make_document(service)
        service.invoke("chunking", analyst, {"document_id": ref.document_id})
        types = [e["event_type"] for e in service.audit_sink.events]
        assert "document.indexed" not in types  # not fully indexed yet
        for op in ("embeddings", "vector_index"):
            service.invoke(op, analyst, {"document_id": ref.document_id})
        types = [e["event_type"] for e in service.audit_sink.events]
        assert types.count("document.indexed") == 1


class TestPermissionMatrix:
    @pytest.mark.parametrize("role,expected_code", [
        ("Auditor", "TOOL_NOT_ALLOWED"),
        ("Restricted User", "TOOL_NOT_ALLOWED"),
    ])
    def test_execute_denied_roles(self, service, role, expected_code):
        ref = make_document(service)
        actor = make_actor(role, clearance="RESTRICTED"
                           if role == "Restricted User" else "INTERNAL")
        with pytest.raises(Exception) as exc:
            service.invoke("chunking", actor, {"document_id": ref.document_id})
        assert getattr(exc.value, "code", "") == expected_code

    @pytest.mark.parametrize("role", [
        "Administrator", "Security Officer", "Operator", "Analyst"])
    def test_execute_allowed_roles(self, service, role):
        ref = make_document(service)
        actor = make_actor(role)
        result = service.invoke("chunking", actor, {"document_id": ref.document_id})
        assert result.data["chunk_count"] >= 1

    def test_read_ops_granted_for_restricted_corpus_level(self, service, analyst):
        # RestrictedUser IS granted Document:read by the canonical matrix; corpus-level
        # read uses a PUBLIC baseline and per-chunk classification filtering hides
        # anything above the caller's clearance (domain/07 Notes).
        _index_doc = make_document(service)
        actor = make_actor("Restricted User", clearance="PUBLIC")
        result = service.invoke("hybrid_search", actor, {"query": "pump"})
        assert "hits" in result.data
        # And the INTERNAL document's chunks are filtered out for this caller:
        service.invoke("chunking", analyst, {"document_id": _index_doc.document_id})
        filtered = service.invoke("hybrid_search", actor, {"query": "pump"})
        assert filtered.data["hits"] == []

    def test_classification_denied_for_low_clearance(self, service, analyst):
        ref = make_document(service, classification="RESTRICTED")
        actor = make_actor("Analyst", clearance="INTERNAL")
        with pytest.raises(Exception) as exc:
            service.invoke("chunking", actor, {"document_id": ref.document_id})
        assert getattr(exc.value, "code", "") == "FILE_CLASSIFICATION_DENIED"

    def test_workspace_mismatch_denied(self, service, analyst):
        ref = make_document(service, workspace="ws-other")
        actor = make_actor("Analyst", workspace="ws-dev")
        with pytest.raises(Exception) as exc:
            service.invoke("chunking", actor, {"document_id": ref.document_id})
        assert getattr(exc.value, "code", "") == "POLICY_DENIED"


class TestRegistryConformance:
    def test_only_registry_codes(self, service, analyst, admin):
        ref = make_document(service)
        attempts = [
            ("chunking", analyst, {"document_id": "missing"}),
            ("chunking", analyst, {"document_id": ref.document_id, "bogus": 1}),
            ("hybrid_search", analyst, {}),
            ("hybrid_search", analyst, {"query": "x", "top_k": 0}),
            ("reranking", analyst, {"query": "x"}),
        ]
        for op, actor, payload in attempts:
            try:
                service.invoke(op, actor, payload)
            except Exception as exc:
                code = getattr(exc, "code", None)
                assert code is not None, f"{op} raised non-registry error: {exc}"
                assert getattr(exc, "http_status", None), "registry code must carry HTTP status"

    def test_invalid_json_shape_rejected(self, service, analyst):
        with pytest.raises(Exception) as exc:
            service.invoke("chunking", analyst, ["not", "a", "dict"])
        assert getattr(exc.value, "code", "") == "INVALID_REQUEST"

    def test_unknown_op_rejected(self, service, analyst):
        with pytest.raises(Exception) as exc:
            service.invoke("definitely_not_an_op", analyst, {})
        assert getattr(exc.value, "code", "") == "INVALID_REQUEST"
