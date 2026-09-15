"""
Live-PostgreSQL integration tests on embedded Postgres (pgserver).

These are the only tests that touch a real database: they validate the actual
SQL (LATERAL join, ILIKE filters, CHECK constraints, upserts) rather than the
query-mapping logic covered by test_database.py's fakes.

Skipped automatically when pgserver is unavailable (e.g. offline CI) — the
fake-based suites still run. Requires: pip install -r requirements-test.txt
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest

pgserver = pytest.importorskip("pgserver")

from app.database import (
    ConflictResolutionRepository,
    EquipmentRepository,
    IncidentRepository,
    InspectionRepository,
    KnowledgeGraphRepository,
    MaintenanceEventRepository,
    PlantRepository,
    UnitRepository,
    get_pool,
    init_schema,
)
from app.entity_resolution import EntityResolver
from app.models import (
    ConflictResolutionCreate,
    ConflictResolutionKind,
    EquipmentCreate,
    EquipmentStatus,
    EquipmentUpdate,
    FindingSeverity,
    IncidentCreate,
    InspectionCreate,
    MaintenanceEventCreate,
    PlantCreate,
    UnitCreate,
)

@pytest.fixture(scope="module")
def pg_uri(tmp_path_factory):
    srv = pgserver.get_server(str(tmp_path_factory.mktemp("pg") / "pgdata"))
    yield srv.get_uri()
    srv.cleanup()


@pytest.fixture(scope="function")
async def pool(pg_uri):
    # Function-scoped so the pool binds to each test's event loop.
    pool = await get_pool(pg_uri)
    await init_schema(pool)
    yield pool
    await pool.close()


@pytest.fixture(scope="function")
async def seed(pool):
    """One plant, two units, one pump per unit sharing tag P-204."""
    plants = PlantRepository(pool)
    units = UnitRepository(pool)
    equipment = EquipmentRepository(pool)
    plant = await plants.create(PlantCreate(organization_id=uuid.uuid4(), name="Refinery"))
    unit_a = await units.create(UnitCreate(plant_id=plant.id, name="CDU-1"))
    unit_b = await units.create(UnitCreate(plant_id=plant.id, name="CDU-2"))
    pump_a = await equipment.create(
        EquipmentCreate(unit_id=unit_a.id, tag_number="P-204", name="Feed Pump")
    )
    pump_b = await equipment.create(
        EquipmentCreate(unit_id=unit_b.id, tag_number="P-204", name="Feed Pump (CDU-2)")
    )
    return {
        "plant": plant,
        "unit_a": unit_a,
        "unit_b": unit_b,
        "pump_a": pump_a,
        "pump_b": pump_b,
    }


class TestAssetLifecycle:
    async def test_search_filters(self, pool, seed):
        repo = EquipmentRepository(pool)
        assert len(await repo.search(seed["plant"].organization_id, tag_number="P-204")) == 2
        assert len(await repo.search(seed["plant"].organization_id, tag_number="P-999")) == 0
        assert len(await repo.search(seed["plant"].organization_id, unit_id=seed["unit_a"].id)) == 1
        assert len(await repo.search(seed["plant"].organization_id, plant_id=seed["plant"].id)) == 2

    async def test_search_pagination(self, pool, seed):
        repo = EquipmentRepository(pool)
        page1 = await repo.search(seed["plant"].organization_id, limit=1, offset=0)
        page2 = await repo.search(seed["plant"].organization_id, limit=1, offset=1)
        assert len(page1) == len(page2) == 1
        assert page1[0].id != page2[0].id

    async def test_update_and_soft_delete(self, pool, seed):
        repo = EquipmentRepository(pool)
        updated = await repo.update(
            seed["pump_a"].id, EquipmentUpdate(status=EquipmentStatus.degraded)
        )
        assert updated.status == EquipmentStatus.degraded
        assert await repo.get(seed["pump_b"].id) is not None
        assert await repo.soft_delete(seed["pump_b"].id) is True
        assert await repo.get(seed["pump_b"].id) is None
        # Soft-deleted rows vanish from search too.
        assert len(await repo.search(seed["plant"].organization_id, tag_number="P-204")) == 1


class TestHistories:
    async def test_maintenance_precise_citation(self, pool, seed):
        repo = MaintenanceEventRepository(pool)
        event = await repo.create(
            MaintenanceEventCreate(
                equipment_id=seed["pump_a"].id,
                event_type="seal replacement",
                performed_at=date(2024, 5, 1),
                technician="J. Doe",
                work_order_id="WO-118",
            )
        )
        assert event.technician == "J. Doe"
        assert event.work_order_id == "WO-118"
        history = await repo.list_by_equipment(seed["pump_a"].id)
        assert history[0].id == event.id

    async def test_inspection_last_date_and_table(self, pool, seed):
        repo = InspectionRepository(pool)
        assert await repo.last_inspection_date(seed["pump_a"].id) is None
        await repo.create(
            InspectionCreate(
                equipment_id=seed["pump_a"].id,
                inspected_at=date(2024, 6, 1),
                finding_summary="torque below spec",
                severity=FindingSeverity.major,
            )
        )
        assert await repo.last_inspection_date(seed["pump_a"].id) == date(2024, 6, 1)
        eq_repo = EquipmentRepository(pool)
        rows = await eq_repo.search_with_history(seed["plant"].organization_id)
        by_id = {e.id: (u, d) for e, u, d in rows}
        assert by_id[seed["pump_a"].id] == ("CDU-1", date(2024, 6, 1))
        assert by_id[seed["pump_b"].id][0] == "CDU-2"

    async def test_incident_round_trip(self, pool, seed):
        repo = IncidentRepository(pool)
        incident = await repo.create(
            IncidentCreate(
                equipment_id=seed["pump_a"].id,
                occurred_at=date(2024, 4, 1),
                description="seal leak",
                severity=FindingSeverity.major,
            )
        )
        assert incident.description == "seal leak"
        assert len(await repo.list_by_equipment(seed["pump_a"].id)) == 1


class TestKnowledgeGraph:
    async def test_entity_resolution_cases(self, pool, seed):
        eq_repo = EquipmentRepository(pool)
        kg_repo = KnowledgeGraphRepository(pool)
        resolver = EntityResolver(eq_repo, kg_repo)
        # Case 1: exact tag in the same unit.
        r1 = await resolver.resolve("P-204", seed["unit_a"].id, seed["plant"].id)
        assert r1.confidence == "exact_same_unit"
        assert r1.requires_human_confirmation is False
        # Case 3: unknown tag.
        r3 = await resolver.resolve("X-999", seed["unit_a"].id, seed["plant"].id)
        assert r3.confidence == "no_match"

    async def test_governed_by_lifecycle(self, pool, seed):
        repo = KnowledgeGraphRepository(pool)
        doc = uuid.uuid4()
        pump = seed["pump_a"].id
        # Idempotent upsert: linking twice keeps one edge.
        await repo.add_governing_document(pump, doc, "SOP")
        await repo.add_governing_document(pump, doc, "SOP updated")
        links = await repo.get_governing_documents(pump)
        assert len(links) == 1
        assert links[0].relationship_note == "SOP updated"
        assert await repo.get_equipment_for_document(doc) == [pump]
        assert await repo.remove_governing_document(pump, doc) is True
        assert await repo.get_governing_documents(pump) == []

    async def test_shared_equipment_join(self, pool, seed):
        repo = KnowledgeGraphRepository(pool)
        doc_a, doc_b = uuid.uuid4(), uuid.uuid4()
        pump = seed["pump_a"].id
        await repo.add_governing_document(pump, doc_a)
        await repo.add_governing_document(pump, doc_b)
        shared = await repo.get_shared_equipment_for_documents(doc_a, doc_b)
        assert shared == [pump]


class TestConflictResolutions:
    async def test_record_and_list(self, pool, seed):
        repo = ConflictResolutionRepository(pool)
        pump = seed["pump_a"].id
        out = await repo.record(
            ConflictResolutionCreate(
                equipment_id=pump,
                claim_description="Filter interval",
                source_a_document_id=uuid.uuid4(),
                source_b_document_id=uuid.uuid4(),
                resolution_kind=ConflictResolutionKind.acknowledge_both,
                resolution_note="Both valid",
            ),
            resolved_by="op-1",
        )
        assert out.resolved_by == "op-1"
        history = await repo.list_by_equipment(pump)
        assert len(history) == 1
        assert history[0].resolution_note == "Both valid"


class TestLifespan:
    def test_startup_initialises_schema(self, pg_uri):
        """Lifespan connects and runs DDL."""
        import os
        from unittest.mock import patch

        from fastapi.testclient import TestClient

        from app import main

        assert main._pool is None
        try:
            with patch.dict(os.environ, {"DATABASE_URL": pg_uri}):
                with TestClient(main.app) as client:
                    assert client.get("/healthz").status_code == 200
                    assert main._pool is not None
        finally:
            main._pool = None
