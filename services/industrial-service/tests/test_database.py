"""
Repository tests using a fake asyncpg pool — no live PostgreSQL required.

Each test drives a repository method against a FakePool that records the SQL
and returns canned dict rows, then asserts on the mapped models and the
query shape (filters, pagination, ordering).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest

from app.database import (
    ConflictResolutionRepository,
    EquipmentRepository,
    IncidentRepository,
    InspectionRepository,
    KnowledgeGraphRepository,
    MaintenanceEventRepository,
    PlantRepository,
    UnitRepository,
)
from app.models import (
    ConflictResolutionCreate,
    ConflictResolutionKind,
    EquipmentCreate,
    EquipmentStatus,
    FindingSeverity,
    IncidentCreate,
    InspectionCreate,
    MaintenanceEventCreate,
)

NOW = datetime.now(timezone.utc)


class FakeConn:
    def __init__(self, fetch_result=None, fetchrow_result=None, execute_result=""):
        self._fetch = fetch_result if fetch_result is not None else []
        self._fetchrow = fetchrow_result
        self._execute = execute_result
        self.calls: list[tuple] = []

    async def fetch(self, sql, *args):
        self.calls.append(("fetch", sql, args))
        return self._fetch

    async def fetchrow(self, sql, *args):
        self.calls.append(("fetchrow", sql, args))
        return self._fetchrow

    async def execute(self, sql, *args):
        self.calls.append(("execute", sql, args))
        return self._execute


class FakeAcquire:
    def __init__(self, conn: FakeConn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, *args):
        return False


class FakePool:
    def __init__(self, conn: FakeConn):
        self._conn = conn

    def acquire(self):
        return FakeAcquire(self._conn)


def _equipment_row(**kwargs):
    row = {
        "id": uuid.uuid4(),
        "unit_id": uuid.uuid4(),
        "tag_number": "P-204",
        "name": "Feed Pump P-204",
        "equipment_type": "pump",
        "manufacturer": "Acme",
        "model_number": "X1",
        "status": "operational",
        "commissioned_at": None,
        "created_at": NOW,
        "deleted_at": None,
    }
    row.update(kwargs)
    return row


def _maintenance_row(**kwargs):
    row = {
        "id": uuid.uuid4(),
        "equipment_id": uuid.uuid4(),
        "source_document_id": None,
        "event_type": "seal replacement",
        "performed_at": date(2024, 5, 1),
        "technician": "J. Doe",
        "work_order_id": "WO-118",
        "notes": None,
        "created_at": NOW,
    }
    row.update(kwargs)
    return row


ORG_ID = uuid.uuid4()


class TestEquipmentRepository:
    @pytest.mark.asyncio
    async def test_get_returns_none_when_missing(self):
        repo = EquipmentRepository(FakePool(FakeConn(fetchrow_result=None)))
        assert await repo.get(uuid.uuid4()) is None

    @pytest.mark.asyncio
    async def test_get_maps_row(self):
        row = _equipment_row()
        repo = EquipmentRepository(FakePool(FakeConn(fetchrow_result=row)))
        equipment = await repo.get(row["id"])
        assert equipment.tag_number == "P-204"
        assert equipment.status == EquipmentStatus.operational

    @pytest.mark.asyncio
    async def test_search_applies_filters_and_pagination(self):
        conn = FakeConn(fetch_result=[_equipment_row(), _equipment_row()])
        repo = EquipmentRepository(FakePool(conn))
        out = await repo.search(
            ORG_ID, tag_number="P-2", status=EquipmentStatus.down, limit=10, offset=5
        )
        assert len(out) == 2
        method, sql, args = conn.calls[0]
        assert method == "fetch"
        assert "ILIKE" in sql and "LIMIT" in sql and "OFFSET" in sql
        # args: org + tag + status + limit + offset
        assert args[0] == ORG_ID and args[-2:] == (10, 5)

    @pytest.mark.asyncio
    async def test_search_with_history_maps_tuple(self):
        row = _equipment_row(unit_name="CDU-2", last_inspection_date=date(2024, 6, 1))
        conn = FakeConn(fetch_result=[row])
        repo = EquipmentRepository(FakePool(conn))
        out = await repo.search_with_history(ORG_ID)
        assert len(out) == 1
        equipment, unit_name, last_date = out[0]
        assert equipment.tag_number == "P-204"
        assert unit_name == "CDU-2"
        assert last_date == date(2024, 6, 1)
        assert "LATERAL" in conn.calls[0][1]

    @pytest.mark.asyncio
    async def test_find_by_tag_in_unit_none(self):
        repo = EquipmentRepository(FakePool(FakeConn(fetchrow_result=None)))
        assert await repo.find_by_tag_in_unit("P-999", uuid.uuid4()) is None


class TestMaintenanceEventRepository:
    @pytest.mark.asyncio
    async def test_create_passes_technician_fields(self):
        row = _maintenance_row()
        conn = FakeConn(fetchrow_result=row)
        repo = MaintenanceEventRepository(FakePool(conn))
        out = await repo.create(
            MaintenanceEventCreate(
                equipment_id=row["equipment_id"],
                technician="J. Doe",
                work_order_id="WO-118",
            )
        )
        assert out.technician == "J. Doe"
        assert out.work_order_id == "WO-118"
        assert conn.calls[0][2][4:6] == ("J. Doe", "WO-118")

    @pytest.mark.asyncio
    async def test_list_paginates(self):
        conn = FakeConn(fetch_result=[_maintenance_row()])
        repo = MaintenanceEventRepository(FakePool(conn))
        out = await repo.list_by_equipment(uuid.uuid4(), limit=5, offset=10)
        assert len(out) == 1
        assert conn.calls[0][2][1:] == (5, 10)


class TestInspectionRepository:
    @pytest.mark.asyncio
    async def test_last_inspection_date_none_row(self):
        repo = InspectionRepository(FakePool(FakeConn(fetchrow_result=None)))
        assert await repo.last_inspection_date(uuid.uuid4()) is None

    @pytest.mark.asyncio
    async def test_last_inspection_date_value(self):
        repo = InspectionRepository(
            FakePool(FakeConn(fetchrow_result={"last": date(2024, 6, 1)}))
        )
        assert await repo.last_inspection_date(uuid.uuid4()) == date(2024, 6, 1)


class TestIncidentRepository:
    @pytest.mark.asyncio
    async def test_list_orders_and_paginates(self):
        row = {
            "id": uuid.uuid4(),
            "equipment_id": uuid.uuid4(),
            "source_document_id": None,
            "occurred_at": date(2024, 4, 1),
            "description": "leak",
            "severity": "major",
            "created_at": NOW,
        }
        conn = FakeConn(fetch_result=[row])
        repo = IncidentRepository(FakePool(conn))
        out = await repo.list_by_equipment(uuid.uuid4())
        assert out[0].description == "leak"
        assert "ORDER BY occurred_at DESC" in conn.calls[0][1]


class TestKnowledgeGraphRepository:
    @pytest.mark.asyncio
    async def test_add_is_idempotent_upsert(self):
        eid, did = uuid.uuid4(), uuid.uuid4()
        conn = FakeConn(
            fetchrow_result={
                "equipment_id": eid,
                "document_id": did,
                "relationship_note": "SOP",
            }
        )
        repo = KnowledgeGraphRepository(FakePool(conn))
        link = await repo.add_governing_document(eid, did, "SOP")
        assert link.equipment_id == eid
        assert "ON CONFLICT" in conn.calls[0][1]

    @pytest.mark.asyncio
    async def test_remove_true_and_false(self):
        repo = KnowledgeGraphRepository(FakePool(FakeConn(execute_result="DELETE 1")))
        assert await repo.remove_governing_document(uuid.uuid4(), uuid.uuid4()) is True
        repo2 = KnowledgeGraphRepository(FakePool(FakeConn(execute_result="DELETE 0")))
        assert (
            await repo2.remove_governing_document(uuid.uuid4(), uuid.uuid4()) is False
        )

    @pytest.mark.asyncio
    async def test_get_equipment_for_document(self):
        eid = uuid.uuid4()
        repo = KnowledgeGraphRepository(
            FakePool(FakeConn(fetch_result=[{"equipment_id": eid}]))
        )
        assert await repo.get_equipment_for_document(uuid.uuid4()) == [eid]


class TestConflictResolutionRepository:
    @pytest.mark.asyncio
    async def test_record_round_trip(self):
        eid, da, db = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        conn = FakeConn(
            fetchrow_result={
                "id": uuid.uuid4(),
                "equipment_id": eid,
                "claim_description": "Filter interval",
                "source_a_document_id": da,
                "source_b_document_id": db,
                "resolution_kind": "acknowledge_both",
                "resolution_note": "Both valid",
                "resolved_by": "op-1",
                "resolved_at": NOW,
            }
        )
        repo = ConflictResolutionRepository(FakePool(conn))
        out = await repo.record(
            ConflictResolutionCreate(
                equipment_id=eid,
                claim_description="Filter interval",
                source_a_document_id=da,
                source_b_document_id=db,
                resolution_kind=ConflictResolutionKind.acknowledge_both,
                resolution_note="Both valid",
            ),
            resolved_by="op-1",
        )
        assert out.resolved_by == "op-1"
        assert out.resolution_kind == ConflictResolutionKind.acknowledge_both


class TestRemainingBranches:
    @pytest.mark.asyncio
    async def test_search_name_filter(self):
        conn = FakeConn(fetch_result=[])
        await EquipmentRepository(FakePool(conn)).search(ORG_ID, name_query="Pump")
        assert "e.name ILIKE" in conn.calls[0][1]

    @pytest.mark.asyncio
    async def test_search_with_history_all_filters(self):
        conn = FakeConn(fetch_result=[])
        await EquipmentRepository(FakePool(conn)).search_with_history(
            ORG_ID, tag_number="P", name_query="Pump",
            status=EquipmentStatus.operational,
            plant_id=uuid.uuid4(), unit_id=uuid.uuid4(),
        )
        sql = conn.calls[0][1]
        assert "ILIKE" in sql and "LIMIT" in sql

    @pytest.mark.asyncio
    async def test_update_all_fields(self):
        from datetime import date as date_cls

        from app.models import EquipmentUpdate

        row = _equipment_row()
        conn = FakeConn(fetchrow_result=row)
        out = await EquipmentRepository(FakePool(conn)).update(
            row["id"],
            EquipmentUpdate(
                status=EquipmentStatus.down, equipment_type="pump",
                manufacturer="Acme", model_number="X2",
                commissioned_at=date_cls(2020, 1, 1),
            ),
        )
        assert out is not None
        assert "commissioned_at" in conn.calls[0][1]

    @pytest.mark.asyncio
    async def test_inspection_and_incident_lists(self):
        from app.database import IncidentRepository, InspectionRepository

        irepo = InspectionRepository(FakePool(FakeConn(fetch_result=[])))
        assert await irepo.list_by_equipment(uuid.uuid4()) == []
        nrepo = IncidentRepository(FakePool(FakeConn(fetch_result=[])))
        assert await nrepo.list_by_equipment(uuid.uuid4()) == []


class TestUncoveredBranches:
    @pytest.mark.asyncio
    async def test_equipment_create(self):
        row = _equipment_row()
        repo = EquipmentRepository(FakePool(FakeConn(fetchrow_result=row)))
        out = await repo.create(
            EquipmentCreate(unit_id=row["unit_id"], tag_number="P-204", name="Feed Pump")
        )
        assert out.tag_number == "P-204"

    @pytest.mark.asyncio
    async def test_search_plant_unit_filters(self):
        conn = FakeConn(fetch_result=[])
        repo = EquipmentRepository(FakePool(conn))
        await repo.search(ORG_ID, plant_id=uuid.uuid4(), unit_id=uuid.uuid4())
        assert "p.id" in conn.calls[0][1] and "u.id" in conn.calls[0][1]

    @pytest.mark.asyncio
    async def test_find_by_tag_in_plant(self):
        conn = FakeConn(fetch_result=[_equipment_row(), _equipment_row()])
        repo = EquipmentRepository(FakePool(conn))
        assert len(await repo.find_by_tag_in_plant("P-204", uuid.uuid4(), uuid.uuid4())) == 2

    @pytest.mark.asyncio
    async def test_plant_get_and_list(self):
        prow = {
            "id": uuid.uuid4(), "organization_id": ORG_ID, "name": "R",
            "location": None, "created_at": NOW, "deleted_at": None,
        }
        repo = PlantRepository(FakePool(FakeConn(fetchrow_result=prow, fetch_result=[prow])))
        assert (await repo.get(prow["id"])).name == "R"
        assert len(await repo.list_by_org(ORG_ID)) == 1

    @pytest.mark.asyncio
    async def test_unit_get_and_soft_delete(self):
        urow = {
            "id": uuid.uuid4(), "plant_id": uuid.uuid4(), "name": "U",
            "unit_type": None, "created_at": NOW, "deleted_at": None,
        }
        conn = FakeConn(fetchrow_result=urow, execute_result="UPDATE 1")
        repo = UnitRepository(FakePool(conn))
        assert (await repo.get(urow["id"])).name == "U"
        assert await repo.soft_delete(urow["id"]) is True

    @pytest.mark.asyncio
    async def test_inspection_and_incident_create(self):
        irow = {
            "id": uuid.uuid4(), "equipment_id": uuid.uuid4(),
            "source_document_id": None, "inspected_at": date(2024, 6, 1),
            "finding_summary": "ok", "severity": "minor", "created_at": NOW,
        }
        irepo = InspectionRepository(FakePool(FakeConn(fetchrow_result=irow)))
        out = await irepo.create(InspectionCreate(equipment_id=irow["equipment_id"]))
        assert out.finding_summary == "ok"
        nrow = {
            "id": uuid.uuid4(), "equipment_id": uuid.uuid4(),
            "source_document_id": None, "occurred_at": date(2024, 4, 1),
            "description": "leak", "severity": None, "created_at": NOW,
        }
        nrepo = IncidentRepository(FakePool(FakeConn(fetchrow_result=nrow)))
        assert (await nrepo.create(IncidentCreate(equipment_id=nrow["equipment_id"]))).description == "leak"

    @pytest.mark.asyncio
    async def test_graph_reads_and_resolution_list(self):
        eid = uuid.uuid4()
        conn = FakeConn(fetch_result=[{"equipment_id": eid}])
        repo = KnowledgeGraphRepository(FakePool(conn))
        assert await repo.get_equipment_for_document(uuid.uuid4()) == [eid]
        assert await repo.get_shared_equipment_for_documents(uuid.uuid4(), uuid.uuid4()) == [eid]
        rrow = {
            "id": uuid.uuid4(), "equipment_id": eid, "claim_description": "c",
            "source_a_document_id": uuid.uuid4(), "source_b_document_id": uuid.uuid4(),
            "resolution_kind": "downgrade_authority", "resolution_note": None,
            "resolved_by": "op", "resolved_at": NOW,
        }
        rrepo = ConflictResolutionRepository(FakePool(FakeConn(fetch_result=[rrow])))
        listed = await rrepo.list_by_equipment(eid)
        assert len(listed) == 1 and listed[0].resolved_by == "op"
