"""
Second repository suite: Plant/Unit repos, equipment mutations, DDL smoke,
and the audit helper — all DB-free via fakes.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app import main
from app.database import (
    CREATE_TABLES_SQL,
    EquipmentRepository,
    PlantRepository,
    UnitRepository,
    init_schema,
)
from app.models import EquipmentStatus, EquipmentUpdate, PlantCreate, UnitCreate
from tests.test_database import FakeConn, FakePool, _equipment_row

NOW = datetime.now(timezone.utc)


def _plant_row(**kwargs):
    row = {
        "id": uuid.uuid4(),
        "organization_id": uuid.uuid4(),
        "name": "Vadodara Refinery",
        "location": None,
        "created_at": NOW,
        "deleted_at": None,
    }
    row.update(kwargs)
    return row


def _unit_row(**kwargs):
    row = {
        "id": uuid.uuid4(),
        "plant_id": uuid.uuid4(),
        "name": "CDU-2",
        "unit_type": "distillation",
        "created_at": NOW,
        "deleted_at": None,
    }
    row.update(kwargs)
    return row


class TestPlantRepository:
    @pytest.mark.asyncio
    async def test_create_and_get(self):
        row = _plant_row()
        repo = PlantRepository(FakePool(FakeConn(fetchrow_result=row)))
        out = await repo.create(
            PlantCreate(
                organization_id=row["organization_id"], name="Vadodara Refinery"
            )
        )
        assert out.name == "Vadodara Refinery"
        assert await repo.get(row["id"]) is not None

    @pytest.mark.asyncio
    async def test_soft_delete_true_false(self):
        repo = PlantRepository(FakePool(FakeConn(execute_result="UPDATE 1")))
        assert await repo.soft_delete(uuid.uuid4()) is True
        repo2 = PlantRepository(FakePool(FakeConn(execute_result="UPDATE 0")))
        assert await repo2.soft_delete(uuid.uuid4()) is False


class TestUnitRepository:
    @pytest.mark.asyncio
    async def test_create_and_list(self):
        row = _unit_row()
        conn = FakeConn(fetchrow_result=row, fetch_result=[row])
        repo = UnitRepository(FakePool(conn))
        out = await repo.create(UnitCreate(plant_id=row["plant_id"], name="CDU-2"))
        assert out.name == "CDU-2"
        listed = await repo.list_by_plant(row["plant_id"])
        assert len(listed) == 1


class TestEquipmentMutations:
    @pytest.mark.asyncio
    async def test_update_partial_status(self):
        row = _equipment_row(status="degraded")
        conn = FakeConn(fetchrow_result=row)
        repo = EquipmentRepository(FakePool(conn))
        out = await repo.update(
            row["id"], EquipmentUpdate(status=EquipmentStatus.degraded)
        )
        assert out.status == EquipmentStatus.degraded
        assert "status" in conn.calls[0][1]

    @pytest.mark.asyncio
    async def test_update_no_fields_falls_back_to_get(self):
        row = _equipment_row()
        conn = FakeConn(fetchrow_result=row)
        repo = EquipmentRepository(FakePool(conn))
        out = await repo.update(row["id"], EquipmentUpdate())
        assert out.tag_number == "P-204"
        assert conn.calls[0][1].startswith("SELECT")

    @pytest.mark.asyncio
    async def test_update_missing_returns_none(self):
        repo = EquipmentRepository(FakePool(FakeConn(fetchrow_result=None)))
        assert (
            await repo.update(
                uuid.uuid4(), EquipmentUpdate(status=EquipmentStatus.down)
            )
            is None
        )

    @pytest.mark.asyncio
    async def test_soft_delete(self):
        repo = EquipmentRepository(FakePool(FakeConn(execute_result="UPDATE 1")))
        assert await repo.soft_delete(uuid.uuid4()) is True

    @pytest.mark.asyncio
    async def test_list_by_unit(self):
        conn = FakeConn(fetch_result=[_equipment_row()])
        repo = EquipmentRepository(FakePool(conn))
        assert len(await repo.list_by_unit(uuid.uuid4())) == 1


class TestInitSchema:
    @pytest.mark.asyncio
    async def test_executes_ddl(self):
        conn = FakeConn()
        await init_schema(FakePool(conn))  # type: ignore[arg-type]
        method, sql, _ = conn.calls[0]
        assert method == "execute"
        assert "CREATE TABLE IF NOT EXISTS equipment" in sql
        assert "conflict_resolutions" in sql

    def test_ddl_covers_all_owned_tables(self):
        for table in (
            "plants",
            "units",
            "equipment",
            "maintenance_events",
            "inspections",
            "incidents",
            "equipment_governing_documents",
            "conflict_resolutions",
        ):
            assert table in CREATE_TABLES_SQL


class TestAuditHelper:
    @pytest.mark.asyncio
    async def test_success_posts_event(self, monkeypatch):
        posted = []

        class FakeClient:
            def __init__(self, *a, **k):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

            async def post(self, url, json=None):
                posted.append((url, json))
                return None

        monkeypatch.setattr(main.httpx, "AsyncClient", FakeClient)
        await main._emit_audit_event("create", "Plant", "1", "op-1")
        assert len(posted) == 1
        assert posted[0][1]["action"] == "create"

    @pytest.mark.asyncio
    async def test_failure_is_swallowed(self, monkeypatch):
        class BoomClient:
            def __init__(self, *a, **k):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

            async def post(self, url, json=None):
                raise ConnectionError("audit down")

        monkeypatch.setattr(main.httpx, "AsyncClient", BoomClient)
        # Must not raise — audit failure never rolls back the action.
        await main._emit_audit_event("create", "Plant", "1", "op-1")
