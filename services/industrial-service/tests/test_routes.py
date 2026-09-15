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

import pytest

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


@pytest.fixture(autouse=True)
def _no_audit(monkeypatch):
    """Isolate routes from the audit service (and skip its 2s timeouts)."""
    monkeypatch.setattr(main, "_emit_audit_event", AsyncMock())


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


def _equipment_model(eid: uuid.UUID, uid: uuid.UUID):
    from app.models import Equipment

    return Equipment(
        id=eid,
        unit_id=uid,
        tag_number="P-204",
        name="Feed Pump P-204",
        status=EquipmentStatus.operational,
        created_at=NOW,
    )


class TestEquipmentCrudRoutes:
    def test_create_201(self):
        from app.models import EquipmentCreate

        uid, eid = uuid.uuid4(), uuid.uuid4()
        repo = AsyncMock()
        repo.create.return_value = _equipment_model(eid, uid)
        client = _make_client({main.equipment_repo: lambda: repo})
        r = client.post(
            f"/units/{uid}/equipment",
            json={
                "unit_id": str(uid),
                "tag_number": "P-204",
                "name": "Feed Pump P-204",
            },
            headers=WRITE,
        )
        assert r.status_code == 201
        assert r.json()["tag_number"] == "P-204"

    def test_create_unit_mismatch_400(self):
        client = _make_client({main.equipment_repo: lambda: AsyncMock()})
        r = client.post(
            f"/units/{uuid.uuid4()}/equipment",
            json={
                "unit_id": str(uuid.uuid4()),
                "tag_number": "P-204",
                "name": "Feed Pump P-204",
            },
            headers=WRITE,
        )
        assert r.status_code == 400

    def test_update_404(self):
        repo = AsyncMock()
        repo.update.return_value = None
        client = _make_client({main.equipment_repo: lambda: repo})
        r = client.patch(
            f"/assets/{uuid.uuid4()}", json={"status": "down"}, headers=WRITE
        )
        assert r.status_code == 404

    def test_delete_204_and_404(self):
        repo = AsyncMock()
        repo.soft_delete.return_value = True
        client = _make_client({main.equipment_repo: lambda: repo})
        assert (
            client.delete(f"/assets/{uuid.uuid4()}", headers=WRITE).status_code == 204
        )
        repo.soft_delete.return_value = False
        assert (
            client.delete(f"/assets/{uuid.uuid4()}", headers=WRITE).status_code == 404
        )


class TestGraphRoutes:
    def test_add_and_remove_governing_document(self):
        from app.models import GoverningDocumentLink

        eid, did = uuid.uuid4(), uuid.uuid4()
        eq = AsyncMock()
        eq.get.return_value = _equipment_model(eid, uuid.uuid4())
        graph = AsyncMock()
        graph.add_governing_document.return_value = GoverningDocumentLink(
            equipment_id=eid, document_id=did, relationship_note="SOP"
        )
        graph.remove_governing_document.return_value = True
        client = _make_client(
            {main.equipment_repo: lambda: eq, main.graph_repo: lambda: graph}
        )
        r = client.post(
            f"/assets/{eid}/governing-documents",
            json={"document_id": str(did), "relationship_note": "SOP"},
            headers=WRITE,
        )
        assert r.status_code == 201
        r = client.delete(f"/assets/{eid}/governing-documents/{did}", headers=WRITE)
        assert r.status_code == 204
        graph.remove_governing_document.return_value = False
        r = client.delete(f"/assets/{eid}/governing-documents/{did}", headers=WRITE)
        assert r.status_code == 404

    def test_documents_equipment_impact(self):
        eid = uuid.uuid4()
        graph = AsyncMock()
        graph.get_equipment_for_document.return_value = [eid]
        client = _make_client({main.graph_repo: lambda: graph})
        r = client.get(f"/documents/{uuid.uuid4()}/equipment", headers=READ)
        assert r.status_code == 200
        assert r.json()["equipment_ids"] == [str(eid)]

    def test_conflict_resolutions_list(self):
        repo = AsyncMock()
        repo.list_by_equipment.return_value = []
        client = _make_client({main.conflict_resolution_repo: lambda: repo})
        r = client.get(f"/assets/{uuid.uuid4()}/conflict-resolutions", headers=READ)
        assert r.status_code == 200
        assert r.json() == []


class TestDetailSuccess:
    def test_detail_200_aggregates(self):
        from app.models import Plant, Unit

        eid, uid, pid = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        eq = AsyncMock()
        eq.get.return_value = _equipment_model(eid, uid)
        unit = AsyncMock()
        unit.get.return_value = Unit(id=uid, plant_id=pid, name="CDU-2", created_at=NOW)
        plant = AsyncMock()
        plant.get.return_value = Plant(
            id=pid, organization_id=uuid.uuid4(), name="Refinery", created_at=NOW
        )
        maint, insp, inci, graph, res = (AsyncMock() for _ in range(5))
        maint.list_by_equipment.return_value = []
        insp.list_by_equipment.return_value = []
        insp.last_inspection_date.return_value = date(2024, 6, 1)
        inci.list_by_equipment.return_value = []
        graph.get_governing_documents.return_value = []
        res.list_by_equipment.return_value = []
        client = _make_client(
            {
                main.equipment_repo: lambda: eq,
                main.unit_repo: lambda: unit,
                main.plant_repo: lambda: plant,
                main.maintenance_repo: lambda: maint,
                main.inspection_repo: lambda: insp,
                main.incident_repo: lambda: inci,
                main.graph_repo: lambda: graph,
                main.conflict_resolution_repo: lambda: res,
            }
        )
        r = client.get(f"/assets/{eid}/detail", headers=READ)
        assert r.status_code == 200
        body = r.json()
        assert body["plant"]["name"] == "Refinery"
        assert body["last_inspection_date"] == "2024-06-01"
        assert body["conflict_resolutions"] == []


class TestValidateAnswerPositives:
    def test_sop_with_disclaimer_valid(self):
        client = _make_client()
        r = client.post(
            "/internal/validate-answer",
            json={
                "answer_text": "Matches Step 3, based on the text of the SOP "
                "document provided, not an independent regulatory assessment.",
                "answer_kind": "sop",
            },
            headers=READ,
        )
        assert r.json() == {"valid": True, "missing": []}


class TestPlantUnitRoutes:
    def test_plant_crud(self):
        from app.models import Plant

        pid, oid = uuid.uuid4(), uuid.uuid4()
        repo = AsyncMock()
        repo.create.return_value = Plant(
            id=pid, organization_id=oid, name="Refinery", created_at=NOW
        )
        repo.get.return_value = repo.create.return_value
        repo.list_by_org.return_value = [repo.create.return_value]
        client = _make_client({main.plant_repo: lambda: repo})
        assert (
            client.post(
                "/plants",
                json={"organization_id": str(oid), "name": "Refinery"},
                headers=WRITE,
            ).status_code
            == 201
        )
        assert client.get(f"/plants/{pid}", headers=READ).status_code == 200
        assert (
            client.get(f"/organizations/{oid}/plants", headers=READ).status_code == 200
        )

    def test_unit_routes(self):
        from app.models import Unit

        uid, pid = uuid.uuid4(), uuid.uuid4()
        repo = AsyncMock()
        repo.create.return_value = Unit(
            id=uid, plant_id=pid, name="CDU-2", created_at=NOW
        )
        repo.get.return_value = repo.create.return_value
        repo.list_by_plant.return_value = [repo.create.return_value]
        client = _make_client({main.unit_repo: lambda: repo})
        assert (
            client.post(
                "/units", json={"plant_id": str(pid), "name": "CDU-2"}, headers=WRITE
            ).status_code
            == 201
        )
        assert client.get(f"/units/{uid}", headers=READ).status_code == 200
        assert client.get(f"/plants/{pid}/units", headers=READ).status_code == 200


class TestRemainingRoutes:
    def test_equipment_get_200(self):
        eid, uid = uuid.uuid4(), uuid.uuid4()
        client = _make_client(
            {main.equipment_repo: lambda: _equipment_repo(_equipment_model(eid, uid))}
        )
        r = client.get(f"/assets/{eid}", headers=READ)
        assert r.status_code == 200
        assert r.json()["tag_number"] == "P-204"

    def test_equipment_get_404(self):
        client = _make_client({main.equipment_repo: lambda: _equipment_repo()})
        assert client.get(f"/assets/{uuid.uuid4()}", headers=READ).status_code == 404

    def test_governing_documents_get(self):
        graph = AsyncMock()
        graph.get_governing_documents.return_value = []
        client = _make_client(
            {
                main.equipment_repo: lambda: _equipment_repo(),
                main.graph_repo: lambda: graph,
            }
        )
        assert (
            client.get(
                f"/assets/{uuid.uuid4()}/governing-documents", headers=READ
            ).status_code
            == 200
        )

    def test_healthz(self):
        assert _make_client().get("/healthz").status_code == 200

    def test_confirm_link_404_and_201(self):
        from app.models import EntityResolutionResult

        eq = AsyncMock()
        eq.get.return_value = None
        resolver = AsyncMock()
        client = _make_client(
            {main.equipment_repo: lambda: eq, main.entity_resolver: lambda: resolver}
        )
        body = {
            "equipment_id": str(uuid.uuid4()),
            "document_id": str(uuid.uuid4()),
        }
        assert (
            client.post("/internal/confirm-link", json=body, headers=WRITE).status_code
            == 404
        )
        eq.get.return_value = AsyncMock()
        assert (
            client.post("/internal/confirm-link", json=body, headers=WRITE).status_code
            == 201
        )

    def test_resolve_tag_success(self):
        from app.models import EntityResolutionResult

        resolver = AsyncMock()
        resolver.resolve.return_value = EntityResolutionResult(
            tag_number="P-204",
            confidence="exact_same_unit",
            matched_equipment_id=uuid.uuid4(),
            requires_human_confirmation=False,
            reason="ok",
        )
        client = _make_client({main.entity_resolver: lambda: resolver})
        r = client.post(
            "/internal/resolve-tag",
            json={
                "tag_number": "P-204",
                "within_unit_id": str(uuid.uuid4()),
                "plant_id": str(uuid.uuid4()),
            },
            headers=READ,
        )
        assert r.status_code == 200
        assert r.json()["confidence"] == "exact_same_unit"


class TestHistoryCreateRoutes:
    def _repos(self, equipment):
        eq = AsyncMock()
        eq.get.return_value = equipment
        return eq

    def test_maintenance_create_201_and_404(self):
        from app.models import MaintenanceEvent

        eid = uuid.uuid4()
        repo = AsyncMock()
        repo.create.return_value = MaintenanceEvent(
            id=uuid.uuid4(),
            equipment_id=eid,
            performed_at=None,
            created_at=NOW,
        )
        client = _make_client(
            {
                main.equipment_repo: lambda: self._repos(AsyncMock()),
                main.maintenance_repo: lambda: repo,
            }
        )
        body = {"equipment_id": str(eid), "event_type": "service"}
        assert (
            client.post(
                f"/assets/{eid}/maintenance-events", json=body, headers=WRITE
            ).status_code
            == 201
        )
        client2 = _make_client(
            {
                main.equipment_repo: lambda: self._repos(None),
                main.maintenance_repo: lambda: repo,
            }
        )
        assert (
            client2.post(
                f"/assets/{eid}/maintenance-events", json=body, headers=WRITE
            ).status_code
            == 404
        )

    def test_inspection_create_201(self):
        from app.models import Inspection

        eid = uuid.uuid4()
        repo = AsyncMock()
        repo.create.return_value = Inspection(
            id=uuid.uuid4(), equipment_id=eid, created_at=NOW
        )
        client = _make_client(
            {
                main.equipment_repo: lambda: self._repos(AsyncMock()),
                main.inspection_repo: lambda: repo,
            }
        )
        assert (
            client.post(
                f"/assets/{eid}/inspections",
                json={"equipment_id": str(eid)},
                headers=WRITE,
            ).status_code
            == 201
        )

    def test_incident_create_201(self):
        from app.models import Incident

        eid = uuid.uuid4()
        repo = AsyncMock()
        repo.create.return_value = Incident(
            id=uuid.uuid4(), equipment_id=eid, created_at=NOW
        )
        client = _make_client(
            {
                main.equipment_repo: lambda: self._repos(AsyncMock()),
                main.incident_repo: lambda: repo,
            }
        )
        assert (
            client.post(
                f"/assets/{eid}/incidents",
                json={"equipment_id": str(eid)},
                headers=WRITE,
            ).status_code
            == 201
        )

    def test_plant_unit_get_404(self):
        plant, unit = AsyncMock(), AsyncMock()
        plant.get.return_value = None
        unit.get.return_value = None
        client = _make_client(
            {
                main.plant_repo: lambda: plant,
                main.unit_repo: lambda: unit,
            }
        )
        assert client.get(f"/plants/{uuid.uuid4()}", headers=READ).status_code == 404
        assert client.get(f"/units/{uuid.uuid4()}", headers=READ).status_code == 404

    def test_resolve_equipment_mismatch_400(self):
        eid = uuid.uuid4()
        eq = AsyncMock()
        eq.get.return_value = AsyncMock()
        client = _make_client(
            {
                main.equipment_repo: lambda: eq,
                main.conflict_resolution_repo: lambda: AsyncMock(),
            }
        )
        body = {
            "equipment_id": str(uuid.uuid4()),
            "claim_description": "x",
            "source_a_document_id": str(uuid.uuid4()),
            "source_b_document_id": str(uuid.uuid4()),
            "resolution_kind": "acknowledge_both",
        }
        assert (
            client.post(
                f"/assets/{eid}/conflicts/resolve", json=body, headers=RECLASSIFY
            ).status_code
            == 400
        )


class TestRouteGapFillers:
    def test_update_200(self):
        eid = uuid.uuid4()
        repo = AsyncMock()
        repo.update.return_value = _equipment_model(eid, uuid.uuid4())
        client = _make_client({main.equipment_repo: lambda: repo})
        r = client.patch(f"/assets/{eid}", json={"status": "down"}, headers=WRITE)
        assert r.status_code == 200
        assert r.json()["tag_number"] == "P-204"

    def test_history_create_404_and_mismatch(self):
        eid = uuid.uuid4()
        eq = AsyncMock()
        eq.get.return_value = None
        client = _make_client(
            {
                main.equipment_repo: lambda: eq,
                main.inspection_repo: lambda: AsyncMock(),
                main.incident_repo: lambda: AsyncMock(),
                main.maintenance_repo: lambda: AsyncMock(),
            }
        )
        assert (
            client.post(
                f"/assets/{eid}/inspections",
                json={"equipment_id": str(eid)},
                headers=WRITE,
            ).status_code
            == 404
        )
        assert (
            client.post(
                f"/assets/{eid}/incidents",
                json={"equipment_id": str(eid)},
                headers=WRITE,
            ).status_code
            == 404
        )
        other = uuid.uuid4()
        eq.get.return_value = AsyncMock()
        assert (
            client.post(
                f"/assets/{eid}/maintenance-events",
                json={"equipment_id": str(other)},
                headers=WRITE,
            ).status_code
            == 400
        )
        assert (
            client.post(
                f"/assets/{eid}/inspections",
                json={"equipment_id": str(other)},
                headers=WRITE,
            ).status_code
            == 400
        )
        assert (
            client.post(
                f"/assets/{eid}/incidents",
                json={"equipment_id": str(other)},
                headers=WRITE,
            ).status_code
            == 400
        )

    def test_history_lists(self):
        insp, inci = self._empty_history(), self._empty_history()
        client = _make_client(
            {
                main.inspection_repo: lambda: insp,
                main.incident_repo: lambda: inci,
            }
        )
        eid = uuid.uuid4()
        assert client.get(f"/assets/{eid}/inspections", headers=READ).status_code == 200
        assert client.get(f"/assets/{eid}/incidents", headers=READ).status_code == 200

    @staticmethod
    def _empty_history():
        repo = AsyncMock()
        repo.list_by_equipment.return_value = []
        return repo

    def test_verify_convert_and_aggregate_200(self):
        client = _make_client()
        r = client.post(
            "/internal/verify-calculation",
            json={"operation": "convert", "value": 1000.0,
                  "from_unit": "mm", "to_unit": "m"},
            headers=READ,
        )
        assert r.json()["converted_value"] == 1.0
        r = client.post(
            "/internal/verify-calculation",
            json={"operation": "aggregate", "values": [1.0, 2.0, 3.0]},
            headers=READ,
        )
        assert r.json()["result"] == 2.0

    def test_verify_calculation_missing_fields_400(self):
        client = _make_client()
        assert (
            client.post(
                "/internal/verify-calculation",
                json={"operation": "tolerance"},
                headers=READ,
            ).status_code
            == 400
        )
        assert (
            client.post(
                "/internal/verify-calculation",
                json={"operation": "convert", "value": 1.0},
                headers=READ,
            ).status_code
            == 400
        )
        assert (
            client.post(
                "/internal/verify-calculation",
                json={"operation": "aggregate"},
                headers=READ,
            ).status_code
            == 400
        )

    def test_resolve_unknown_equipment_404(self):
        eid = uuid.uuid4()
        eq = AsyncMock()
        eq.get.return_value = None
        client = _make_client(
            {
                main.equipment_repo: lambda: eq,
                main.conflict_resolution_repo: lambda: AsyncMock(),
            }
        )
        body = {
            "equipment_id": str(eid),
            "claim_description": "x",
            "source_a_document_id": str(uuid.uuid4()),
            "source_b_document_id": str(uuid.uuid4()),
            "resolution_kind": "acknowledge_both",
        }
        assert (
            client.post(
                f"/assets/{eid}/conflicts/resolve", json=body, headers=RECLASSIFY
            ).status_code
            == 404
        )

    def test_add_governing_document_unknown_equipment_404(self):
        eq = AsyncMock()
        eq.get.return_value = None
        client = _make_client(
            {
                main.equipment_repo: lambda: eq,
                main.graph_repo: lambda: AsyncMock(),
            }
        )
        assert (
            client.post(
                f"/assets/{uuid.uuid4()}/governing-documents",
                json={"document_id": str(uuid.uuid4())},
                headers=WRITE,
            ).status_code
            == 404
        )
