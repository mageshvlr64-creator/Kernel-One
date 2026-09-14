"""
Route tests with all repository dependencies overridden — no DB, no network.

Audit emission is fire-and-forget (failures swallowed), so no audit mock is
needed. Permission gates are exercised for both allow and deny paths.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app import main
from app.models import EquipmentStatus

NOW = datetime.now(timezone.utc)
READ = {"X-Roles": "Equipment:read"}
WRITE = {"X-Roles": "Equipment:write"}
RECLASSIFY = {"X-Roles": "Document:reclassify"}


def _equipment_dict(eid: uuid.UUID, uid: uuid.UUID):
    return {
        "id": str(eid),
        "unit_id": str(uid),
        "tag_number": "P-204",
        "name": "Feed Pump P-204",
        "equipment_type": "pump",
        "manufacturer": "Acme",
        "model_number": "X1",
        "status": "operational",
        "commissioned_at": None,
        "created_at": NOW.isoformat(),
        "deleted_at": None,
    }


def _make_client(overrides=None):
    main.app.dependency_overrides = overrides or {}
    return TestClient(main.app, raise_server_exceptions=False)


def _equipment_repo(equipment=None):
    repo = AsyncMock()
    repo.get.return_value = equipment
    repo.search.return_value = []
    repo.search_with_history.return_value = []
    return repo


class TestAssetRoutes:
    def test_list_requires_permission(self):
        client = _make_client({main.equipment_repo: lambda: _equipment_repo()})
        r = client.get("/assets", params={"organization_id": str(uuid.uuid4())})
        assert r.status_code == 403

    def test_list_ok(self):
        client = _make_client({main.equipment_repo: lambda: _equipment_repo()})
        r = client.get(
            "/assets",
            params={"organization_id": str(uuid.uuid4())},
            headers=READ,
        )
        assert r.status_code == 200
        assert r.json() == []

    def test_table_ok(self):
        client = _make_client({main.equipment_repo: lambda: _equipment_repo()})
        r = client.get(
            "/assets/table",
            params={"organization_id": str(uuid.uuid4())},
            headers=READ,
        )
        assert r.status_code == 200

    def test_detail_404(self):
        async def get_none(_):
            return None

        eq = AsyncMock()
        eq.get = get_none
        client = _make_client(
            {
                main.equipment_repo: lambda: eq,
                main.unit_repo: lambda: AsyncMock(),
                main.plant_repo: lambda: AsyncMock(),
                main.maintenance_repo: lambda: AsyncMock(),
                main.inspection_repo: lambda: AsyncMock(),
                main.incident_repo: lambda: AsyncMock(),
                main.graph_repo: lambda: AsyncMock(),
                main.conflict_resolution_repo: lambda: AsyncMock(),
            }
        )
        r = client.get(f"/assets/{uuid.uuid4()}/detail", headers=READ)
        assert r.status_code == 404

    def test_history_list_paginates(self):
        repo = AsyncMock()
        repo.list_by_equipment.return_value = []
        client = _make_client({main.maintenance_repo: lambda: repo})
        r = client.get(
            f"/assets/{uuid.uuid4()}/maintenance-events",
            params={"limit": 5, "offset": 10},
            headers=READ,
        )
        assert r.status_code == 200
        repo.list_by_equipment.assert_called_once()
        _, kwargs = repo.list_by_equipment.call_args
        assert kwargs == {"limit": 5, "offset": 10}


class TestInternalRoutes:
    def test_validate_answer_unknown_kind_400(self):
        client = _make_client()
        r = client.post(
            "/internal/validate-answer",
            json={"answer_text": "x", "answer_kind": "nope"},
            headers=READ,
        )
        assert r.status_code == 400

    def test_validate_answer_forbidden_without_roles(self):
        client = _make_client()
        r = client.post(
            "/internal/validate-answer",
            json={"answer_text": "x", "answer_kind": "general"},
        )
        assert r.status_code == 403

    def test_validate_finding_ok(self):
        client = _make_client()
        r = client.post(
            "/internal/validate-finding",
            json={
                "parameter": "torque",
                "measured_value": "150 Nm",
                "specification": "150 Nm",
                "pass_fail": "PASS",
                "evidence_id_parameter": "ev-1",
                "evidence_id_measured_value": "ev-2",
                "evidence_id_specification": "ev-3",
                "evidence_id_pass_fail": "ev-4",
            },
            headers=READ,
        )
        assert r.status_code == 200
        assert r.json()["supported"] is True

    def test_verify_calculation_bad_op_400(self):
        client = _make_client()
        r = client.post(
            "/internal/verify-calculation",
            json={"operation": "guess"},
            headers=READ,
        )
        assert r.status_code == 400

    def test_verify_tolerance_ok(self):
        client = _make_client()
        r = client.post(
            "/internal/verify-calculation",
            json={
                "operation": "tolerance",
                "measured_value": 5.0,
                "spec_min": 1.0,
                "spec_max": 10.0,
            },
            headers=READ,
        )
        assert r.status_code == 200
        assert r.json()["passed"] is True

    def test_check_sop_compliance_rejects(self):
        client = _make_client()
        r = client.post(
            "/internal/check-sop-compliance",
            json={"agent_verdict": "match", "answer_text": "matches, trust me"},
            headers=READ,
        )
        assert r.status_code == 200
        assert r.json()["accepted"] is False

    def test_detect_conflicts_empty(self):
        client = _make_client()
        eid = str(uuid.uuid4())
        r = client.post(
            "/internal/detect-conflicts",
            json={"equipment_id": eid, "claims": []},
            headers=READ,
        )
        assert r.status_code == 200
        assert r.json() == []

    def test_compare_documents_empty(self):
        client = _make_client()
        r = client.post(
            "/internal/compare-documents",
            json={
                "document_a_id": str(uuid.uuid4()),
                "document_b_id": str(uuid.uuid4()),
                "findings_a": [],
                "findings_b": [],
            },
            headers=READ,
        )
        assert r.status_code == 200
        assert r.json()["added"] == []

    def test_resolve_tag_forbidden(self):
        client = _make_client({main.entity_resolver: lambda: AsyncMock()})
        r = client.post(
            "/internal/resolve-tag",
            json={
                "tag_number": "P-204",
                "within_unit_id": str(uuid.uuid4()),
                "plant_id": str(uuid.uuid4()),
            },
        )
        assert r.status_code == 403


class TestResolveConflict:
    def test_requires_reclassify(self):
        client = _make_client(
            {
                main.conflict_resolution_repo: lambda: AsyncMock(),
                main.equipment_repo: lambda: _equipment_repo(),
            }
        )
        eid = uuid.uuid4()
        body = {
            "equipment_id": str(eid),
            "claim_description": "Filter interval",
            "source_a_document_id": str(uuid.uuid4()),
            "source_b_document_id": str(uuid.uuid4()),
            "resolution_kind": "acknowledge_both",
        }
        r = client.post(f"/assets/{eid}/conflicts/resolve", json=body, headers=WRITE)
        assert r.status_code == 403

    def test_records_and_audits(self):
        from app.models import ConflictResolution

        eid = uuid.uuid4()
        resolution = ConflictResolution(
            id=uuid.uuid4(),
            equipment_id=eid,
            claim_description="Filter interval",
            source_a_document_id=uuid.uuid4(),
            source_b_document_id=uuid.uuid4(),
            resolution_kind="acknowledge_both",
            resolution_note=None,
            resolved_by="op-1",
            resolved_at=NOW,
        )
        res_repo = AsyncMock()
        res_repo.record.return_value = resolution
        eq = AsyncMock()
        eq.get.return_value = AsyncMock()  # truthy equipment
        client = _make_client(
            {
                main.conflict_resolution_repo: lambda: res_repo,
                main.equipment_repo: lambda: eq,
            }
        )
        body = {
            "equipment_id": str(eid),
            "claim_description": "Filter interval",
            "source_a_document_id": str(uuid.uuid4()),
            "source_b_document_id": str(uuid.uuid4()),
            "resolution_kind": "acknowledge_both",
        }
        r = client.post(
            f"/assets/{eid}/conflicts/resolve",
            json=body,
            headers={**dict(RECLASSIFY), "X-Actor": "op-1"},
        )
        assert r.status_code == 201
        assert r.json()["resolved_by"] == "op-1"
