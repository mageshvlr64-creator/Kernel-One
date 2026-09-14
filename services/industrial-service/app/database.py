"""
Database layer for industrial-service.

Uses asyncpg directly (no ORM) to keep the queries explicit and auditable.
All tables are defined here as raw SQL DDL — see also infra/migrations/ for the
forward-only migration files that must stay in sync.

Schema reference: docs/domain/20_asset_model.md
Graph reference:  docs/industrial/13_asset_knowledge_graph.md
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Optional

import asyncpg

from app.models import (
    ConflictResolution,
    ConflictResolutionCreate,
    Equipment,
    EquipmentCreate,
    EquipmentStatus,
    EquipmentUpdate,
    FindingSeverity,
    GoverningDocumentLink,
    Incident,
    IncidentCreate,
    Inspection,
    InspectionCreate,
    MaintenanceEvent,
    MaintenanceEventCreate,
    Plant,
    PlantCreate,
    Unit,
    UnitCreate,
)

# ---------------------------------------------------------------------------
# DDL — forward-only migration SQL (also lives in infra/migrations/)
# ---------------------------------------------------------------------------

CREATE_TABLES_SQL = """
-- Plants
CREATE TABLE IF NOT EXISTS plants (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    name            TEXT NOT NULL,
    location        TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at      TIMESTAMPTZ
);

-- Units
CREATE TABLE IF NOT EXISTS units (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plant_id    UUID NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    unit_type   TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at  TIMESTAMPTZ
);

-- Equipment
CREATE TABLE IF NOT EXISTS equipment (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    unit_id         UUID NOT NULL REFERENCES units(id) ON DELETE CASCADE,
    tag_number      TEXT NOT NULL,
    name            TEXT NOT NULL,
    equipment_type  TEXT,
    manufacturer    TEXT,
    model_number    TEXT,
    status          TEXT NOT NULL DEFAULT 'operational'
                        CHECK (status IN ('operational','degraded','down','decommissioned')),
    commissioned_at DATE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at      TIMESTAMPTZ,
    UNIQUE (unit_id, tag_number)   -- tag_number unique within unit per domain model
);

-- MaintenanceEvents
CREATE TABLE IF NOT EXISTS maintenance_events (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id        UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    source_document_id  UUID,          -- FK into documents table owned by Character 3
    event_type          TEXT,
    performed_at        DATE,
    technician          TEXT,          -- docs/industrial/03_maintenance_records.md
    work_order_id       TEXT,          -- docs/industrial/03_maintenance_records.md
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Inspections
CREATE TABLE IF NOT EXISTS inspections (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id        UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    source_document_id  UUID,
    inspected_at        DATE,
    finding_summary     TEXT,
    severity            TEXT CHECK (severity IN ('informational','minor','major','critical')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Incidents
CREATE TABLE IF NOT EXISTS incidents (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id        UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    source_document_id  UUID,
    occurred_at         DATE,
    description         TEXT,
    severity            TEXT CHECK (severity IN ('informational','minor','major','critical')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- governed_by join table (many-to-many: Equipment ↔ Document)
-- Per docs/industrial/13_asset_knowledge_graph.md
CREATE TABLE IF NOT EXISTS equipment_governing_documents (
    equipment_id        UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    document_id         UUID NOT NULL,   -- FK into documents table owned by Character 3
    relationship_note   TEXT,
    PRIMARY KEY (equipment_id, document_id)
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_equipment_unit_id    ON equipment(unit_id)    WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_equipment_tag        ON equipment(tag_number) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_maintenance_equip    ON maintenance_events(equipment_id);
CREATE INDEX IF NOT EXISTS idx_inspections_equip    ON inspections(equipment_id);
CREATE INDEX IF NOT EXISTS idx_incidents_equip      ON incidents(equipment_id);
CREATE INDEX IF NOT EXISTS idx_gov_docs_equip       ON equipment_governing_documents(equipment_id);
CREATE INDEX IF NOT EXISTS idx_gov_docs_document    ON equipment_governing_documents(document_id);

-- Conflict resolutions (human decisions per docs/industrial/14_knowledge_conflict_detection.md).
-- ConflictRecord itself is NOT a table (an Evidence.verification_status pair);
-- this table records the human's resolution so the same conflict is not re-flagged.
CREATE TABLE IF NOT EXISTS conflict_resolutions (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id            UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    claim_description       TEXT NOT NULL,
    source_a_document_id    UUID NOT NULL,
    source_b_document_id    UUID NOT NULL,
    resolution_kind         TEXT NOT NULL
        CHECK (resolution_kind IN ('downgrade_authority','set_effective_until','acknowledge_both')),
    resolution_note         TEXT,
    resolved_by             TEXT NOT NULL,
    resolved_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_conflict_res_equip ON conflict_resolutions(equipment_id);
"""


# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------


async def get_pool(dsn: str) -> asyncpg.Pool:
    """Create and return an asyncpg connection pool."""
    return await asyncpg.create_pool(dsn=dsn)


async def init_schema(pool: asyncpg.Pool) -> None:
    """Idempotently create tables if they don't exist.

    In production this is superseded by infra/migrations/ — this is a
    convenience for tests and fresh local deployments.
    """
    async with pool.acquire() as conn:
        await conn.execute(CREATE_TABLES_SQL)


# ---------------------------------------------------------------------------
# Helper: row → model
# ---------------------------------------------------------------------------


def _row_to_plant(row: asyncpg.Record) -> Plant:
    return Plant(
        id=row["id"],
        organization_id=row["organization_id"],
        name=row["name"],
        location=row["location"],
        created_at=row["created_at"],
        deleted_at=row["deleted_at"],
    )


def _row_to_unit(row: asyncpg.Record) -> Unit:
    return Unit(
        id=row["id"],
        plant_id=row["plant_id"],
        name=row["name"],
        unit_type=row["unit_type"],
        created_at=row["created_at"],
        deleted_at=row["deleted_at"],
    )


def _row_to_equipment(row: asyncpg.Record) -> Equipment:
    return Equipment(
        id=row["id"],
        unit_id=row["unit_id"],
        tag_number=row["tag_number"],
        name=row["name"],
        equipment_type=row["equipment_type"],
        manufacturer=row["manufacturer"],
        model_number=row["model_number"],
        status=EquipmentStatus(row["status"]),
        commissioned_at=row["commissioned_at"],
        created_at=row["created_at"],
        deleted_at=row["deleted_at"],
    )


def _row_to_maintenance_event(row: asyncpg.Record) -> MaintenanceEvent:
    return MaintenanceEvent(
        id=row["id"],
        equipment_id=row["equipment_id"],
        source_document_id=row["source_document_id"],
        event_type=row["event_type"],
        performed_at=row["performed_at"],
        technician=row["technician"] if "technician" in row else None,
        work_order_id=row["work_order_id"] if "work_order_id" in row else None,
        notes=row["notes"],
        created_at=row["created_at"],
    )


def _row_to_inspection(row: asyncpg.Record) -> Inspection:
    return Inspection(
        id=row["id"],
        equipment_id=row["equipment_id"],
        source_document_id=row["source_document_id"],
        inspected_at=row["inspected_at"],
        finding_summary=row["finding_summary"],
        severity=FindingSeverity(row["severity"]) if row["severity"] else None,
        created_at=row["created_at"],
    )


def _row_to_incident(row: asyncpg.Record) -> Incident:
    return Incident(
        id=row["id"],
        equipment_id=row["equipment_id"],
        source_document_id=row["source_document_id"],
        occurred_at=row["occurred_at"],
        description=row["description"],
        severity=FindingSeverity(row["severity"]) if row["severity"] else None,
        created_at=row["created_at"],
    )


# ---------------------------------------------------------------------------
# Plant repository
# ---------------------------------------------------------------------------


class PlantRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create(self, payload: PlantCreate) -> Plant:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO plants (organization_id, name, location)
                VALUES ($1, $2, $3)
                RETURNING *
                """,
                payload.organization_id,
                payload.name,
                payload.location,
            )
        return _row_to_plant(row)

    async def get(self, plant_id: uuid.UUID) -> Optional[Plant]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM plants WHERE id = $1 AND deleted_at IS NULL",
                plant_id,
            )
        return _row_to_plant(row) if row else None

    async def list_by_org(self, organization_id: uuid.UUID) -> list[Plant]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM plants WHERE organization_id = $1 AND deleted_at IS NULL ORDER BY name",
                organization_id,
            )
        return [_row_to_plant(r) for r in rows]

    async def soft_delete(self, plant_id: uuid.UUID) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE plants SET deleted_at = now() WHERE id = $1 AND deleted_at IS NULL",
                plant_id,
            )
        return result == "UPDATE 1"


# ---------------------------------------------------------------------------
# Unit repository
# ---------------------------------------------------------------------------


class UnitRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create(self, payload: UnitCreate) -> Unit:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO units (plant_id, name, unit_type)
                VALUES ($1, $2, $3)
                RETURNING *
                """,
                payload.plant_id,
                payload.name,
                payload.unit_type,
            )
        return _row_to_unit(row)

    async def get(self, unit_id: uuid.UUID) -> Optional[Unit]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM units WHERE id = $1 AND deleted_at IS NULL",
                unit_id,
            )
        return _row_to_unit(row) if row else None

    async def list_by_plant(self, plant_id: uuid.UUID) -> list[Unit]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM units WHERE plant_id = $1 AND deleted_at IS NULL ORDER BY name",
                plant_id,
            )
        return [_row_to_unit(r) for r in rows]

    async def soft_delete(self, unit_id: uuid.UUID) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE units SET deleted_at = now() WHERE id = $1 AND deleted_at IS NULL",
                unit_id,
            )
        return result == "UPDATE 1"


# ---------------------------------------------------------------------------
# Equipment repository
# ---------------------------------------------------------------------------


class EquipmentRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create(self, payload: EquipmentCreate) -> Equipment:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO equipment
                    (unit_id, tag_number, name, equipment_type, manufacturer,
                     model_number, status, commissioned_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING *
                """,
                payload.unit_id,
                payload.tag_number,
                payload.name,
                payload.equipment_type,
                payload.manufacturer,
                payload.model_number,
                payload.status.value,
                payload.commissioned_at,
            )
        return _row_to_equipment(row)

    async def get(self, equipment_id: uuid.UUID) -> Optional[Equipment]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM equipment WHERE id = $1 AND deleted_at IS NULL",
                equipment_id,
            )
        return _row_to_equipment(row) if row else None

    async def list_by_unit(self, unit_id: uuid.UUID) -> list[Equipment]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM equipment WHERE unit_id = $1 AND deleted_at IS NULL ORDER BY tag_number",
                unit_id,
            )
        return [_row_to_equipment(r) for r in rows]

    async def search(
        self,
        organization_id: uuid.UUID,
        tag_number: Optional[str] = None,
        name_query: Optional[str] = None,
        status: Optional[EquipmentStatus] = None,
        plant_id: Optional[uuid.UUID] = None,
        unit_id: Optional[uuid.UUID] = None,
    ) -> list[Equipment]:
        """Search all equipment visible to an organization with optional filters.

        Used by the Asset list view (docs/ui/23_asset_view.md /assets route).
        """
        conditions = [
            "p.organization_id = $1",
            "e.deleted_at IS NULL",
            "u.deleted_at IS NULL",
            "p.deleted_at IS NULL",
        ]
        args: list[Any] = [organization_id]
        idx = 2

        if tag_number:
            conditions.append(f"e.tag_number ILIKE ${idx}")
            args.append(f"%{tag_number}%")
            idx += 1
        if name_query:
            conditions.append(f"e.name ILIKE ${idx}")
            args.append(f"%{name_query}%")
            idx += 1
        if status:
            conditions.append(f"e.status = ${idx}")
            args.append(status.value)
            idx += 1
        if plant_id:
            conditions.append(f"p.id = ${idx}")
            args.append(plant_id)
            idx += 1
        if unit_id:
            conditions.append(f"u.id = ${idx}")
            args.append(unit_id)
            idx += 1

        where = " AND ".join(conditions)
        sql = f"""
            SELECT e.*
            FROM equipment e
            JOIN units u ON u.id = e.unit_id
            JOIN plants p ON p.id = u.plant_id
            WHERE {where}
            ORDER BY e.tag_number
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, *args)
        return [_row_to_equipment(r) for r in rows]

    async def search_with_history(
        self,
        organization_id: uuid.UUID,
        tag_number: Optional[str] = None,
        name_query: Optional[str] = None,
        status: Optional[EquipmentStatus] = None,
        plant_id: Optional[uuid.UUID] = None,
        unit_id: Optional[uuid.UUID] = None,
    ) -> list[tuple[Equipment, Optional[str], Optional[date]]]:
        """Search plus per-row list-view columns in a single query.

        Returns (Equipment, unit_name, last_inspection_date) tuples for the
        Asset list view table (docs/ui/23_asset_view.md: Tag, Name, Unit,
        Status, last inspection date).
        """
        conditions = [
            "p.organization_id = $1",
            "e.deleted_at IS NULL",
            "u.deleted_at IS NULL",
            "p.deleted_at IS NULL",
        ]
        args: list[Any] = [organization_id]
        idx = 2

        if tag_number:
            conditions.append(f"e.tag_number ILIKE ${idx}")
            args.append(f"%{tag_number}%")
            idx += 1
        if name_query:
            conditions.append(f"e.name ILIKE ${idx}")
            args.append(f"%{name_query}%")
            idx += 1
        if status:
            conditions.append(f"e.status = ${idx}")
            args.append(status.value)
            idx += 1
        if plant_id:
            conditions.append(f"p.id = ${idx}")
            args.append(plant_id)
            idx += 1
        if unit_id:
            conditions.append(f"u.id = ${idx}")
            args.append(unit_id)
            idx += 1

        where = " AND ".join(conditions)
        sql = f"""
            SELECT e.*, u.name AS unit_name, insp.last_date AS last_inspection_date
            FROM equipment e
            JOIN units u ON u.id = e.unit_id
            JOIN plants p ON p.id = u.plant_id
            LEFT JOIN LATERAL (
                SELECT MAX(inspected_at) AS last_date
                FROM inspections
                WHERE equipment_id = e.id
            ) insp ON true
            WHERE {where}
            ORDER BY e.tag_number
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, *args)
        return [
            (_row_to_equipment(r), r["unit_name"], r["last_inspection_date"])
            for r in rows
        ]

    async def update(
        self, equipment_id: uuid.UUID, payload: EquipmentUpdate
    ) -> Optional[Equipment]:
        """Partial update — only touches fields the caller explicitly provided."""
        updates: dict[str, Any] = {}
        if payload.status is not None:
            updates["status"] = payload.status.value
        if payload.equipment_type is not None:
            updates["equipment_type"] = payload.equipment_type
        if payload.manufacturer is not None:
            updates["manufacturer"] = payload.manufacturer
        if payload.model_number is not None:
            updates["model_number"] = payload.model_number
        if payload.commissioned_at is not None:
            updates["commissioned_at"] = payload.commissioned_at

        if not updates:
            return await self.get(equipment_id)

        set_clauses = ", ".join(
            f"{col} = ${i + 2}" for i, col in enumerate(updates.keys())
        )
        sql = f"UPDATE equipment SET {set_clauses} WHERE id = $1 AND deleted_at IS NULL RETURNING *"
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, equipment_id, *updates.values())
        return _row_to_equipment(row) if row else None

    async def soft_delete(self, equipment_id: uuid.UUID) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE equipment SET deleted_at = now() WHERE id = $1 AND deleted_at IS NULL",
                equipment_id,
            )
        return result == "UPDATE 1"

    # Entity resolution helpers (docs/industrial/13_asset_knowledge_graph.md)

    async def find_by_tag_in_unit(
        self, tag_number: str, unit_id: uuid.UUID
    ) -> Optional[Equipment]:
        """Exact tag match within the same Unit — highest confidence auto-link."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM equipment WHERE tag_number = $1 AND unit_id = $2 AND deleted_at IS NULL",
                tag_number,
                unit_id,
            )
        return _row_to_equipment(row) if row else None

    async def find_by_tag_in_plant(
        self, tag_number: str, plant_id: uuid.UUID, exclude_unit_id: uuid.UUID
    ) -> list[Equipment]:
        """Exact tag match in a different Unit of the same Plant.

        Returns all matches (may be >1 if reused across units).
        These require human confirmation before being auto-linked.
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT e.*
                FROM equipment e
                JOIN units u ON u.id = e.unit_id
                WHERE e.tag_number = $1
                  AND u.plant_id = $2
                  AND e.unit_id != $3
                  AND e.deleted_at IS NULL
                  AND u.deleted_at IS NULL
                """,
                tag_number,
                plant_id,
                exclude_unit_id,
            )
        return [_row_to_equipment(r) for r in rows]


# ---------------------------------------------------------------------------
# MaintenanceEvent repository
# ---------------------------------------------------------------------------


class MaintenanceEventRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create(self, payload: MaintenanceEventCreate) -> MaintenanceEvent:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO maintenance_events
                    (equipment_id, source_document_id, event_type, performed_at,
                     technician, work_order_id, notes)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING *
                """,
                payload.equipment_id,
                payload.source_document_id,
                payload.event_type,
                payload.performed_at,
                payload.technician,
                payload.work_order_id,
                payload.notes,
            )
        return _row_to_maintenance_event(row)

    async def list_by_equipment(
        self, equipment_id: uuid.UUID
    ) -> list[MaintenanceEvent]:
        """Chronological — most recent first, per ui/23_asset_view.md."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM maintenance_events
                WHERE equipment_id = $1
                ORDER BY performed_at DESC NULLS LAST, created_at DESC
                """,
                equipment_id,
            )
        return [_row_to_maintenance_event(r) for r in rows]


# ---------------------------------------------------------------------------
# Inspection repository
# ---------------------------------------------------------------------------


class InspectionRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create(self, payload: InspectionCreate) -> Inspection:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO inspections
                    (equipment_id, source_document_id, inspected_at, finding_summary, severity)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING *
                """,
                payload.equipment_id,
                payload.source_document_id,
                payload.inspected_at,
                payload.finding_summary,
                payload.severity.value if payload.severity else None,
            )
        return _row_to_inspection(row)

    async def list_by_equipment(self, equipment_id: uuid.UUID) -> list[Inspection]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM inspections
                WHERE equipment_id = $1
                ORDER BY inspected_at DESC NULLS LAST, created_at DESC
                """,
                equipment_id,
            )
        return [_row_to_inspection(r) for r in rows]

    async def last_inspection_date(self, equipment_id: uuid.UUID) -> Optional[date]:
        """Used by the Asset list view to show last inspection date."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT MAX(inspected_at) AS last FROM inspections WHERE equipment_id = $1",
                equipment_id,
            )
        return row["last"] if row else None


# ---------------------------------------------------------------------------
# Incident repository
# ---------------------------------------------------------------------------


class IncidentRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create(self, payload: IncidentCreate) -> Incident:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO incidents
                    (equipment_id, source_document_id, occurred_at, description, severity)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING *
                """,
                payload.equipment_id,
                payload.source_document_id,
                payload.occurred_at,
                payload.description,
                payload.severity.value if payload.severity else None,
            )
        return _row_to_incident(row)

    async def list_by_equipment(self, equipment_id: uuid.UUID) -> list[Incident]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM incidents
                WHERE equipment_id = $1
                ORDER BY occurred_at DESC NULLS LAST, created_at DESC
                """,
                equipment_id,
            )
        return [_row_to_incident(r) for r in rows]


# ---------------------------------------------------------------------------
# KnowledgeGraph repository (governed_by join table)
# ---------------------------------------------------------------------------


class KnowledgeGraphRepository:
    """Manages the governed_by edges between Equipment and Documents.

    See docs/industrial/13_asset_knowledge_graph.md for the full relationship model.
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def add_governing_document(
        self,
        equipment_id: uuid.UUID,
        document_id: uuid.UUID,
        relationship_note: Optional[str] = None,
    ) -> GoverningDocumentLink:
        """Add a governed_by edge.  Idempotent on (equipment_id, document_id)."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO equipment_governing_documents
                    (equipment_id, document_id, relationship_note)
                VALUES ($1, $2, $3)
                ON CONFLICT (equipment_id, document_id) DO UPDATE
                    SET relationship_note = EXCLUDED.relationship_note
                RETURNING *
                """,
                equipment_id,
                document_id,
                relationship_note,
            )
        return GoverningDocumentLink(
            equipment_id=row["equipment_id"],
            document_id=row["document_id"],
            relationship_note=row["relationship_note"],
        )

    async def remove_governing_document(
        self, equipment_id: uuid.UUID, document_id: uuid.UUID
    ) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM equipment_governing_documents WHERE equipment_id = $1 AND document_id = $2",
                equipment_id,
                document_id,
            )
        return result == "DELETE 1"

    async def get_governing_documents(
        self, equipment_id: uuid.UUID
    ) -> list[GoverningDocumentLink]:
        """Return all documents governing a piece of equipment."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM equipment_governing_documents WHERE equipment_id = $1",
                equipment_id,
            )
        return [
            GoverningDocumentLink(
                equipment_id=r["equipment_id"],
                document_id=r["document_id"],
                relationship_note=r["relationship_note"],
            )
            for r in rows
        ]

    async def get_equipment_for_document(
        self, document_id: uuid.UUID
    ) -> list[uuid.UUID]:
        """Return all equipment_ids governed by a given document.

        Used during conflict detection to scope the check to equipment already
        sharing this document via a governed_by edge.
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT equipment_id FROM equipment_governing_documents WHERE document_id = $1",
                document_id,
            )
        return [r["equipment_id"] for r in rows]

    async def get_shared_equipment_for_documents(
        self, document_id_a: uuid.UUID, document_id_b: uuid.UUID
    ) -> list[uuid.UUID]:
        """Return equipment_ids that are governed_by BOTH documents.

        This is the structural join that triggers conflict detection:
        two documents both governing the same piece of equipment with
        conflicting claims.
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT a.equipment_id
                FROM equipment_governing_documents a
                JOIN equipment_governing_documents b
                  ON a.equipment_id = b.equipment_id
                WHERE a.document_id = $1
                  AND b.document_id = $2
                """,
                document_id_a,
                document_id_b,
            )
        return [r["equipment_id"] for r in rows]


# ---------------------------------------------------------------------------
# ConflictResolution repository (human decisions — never automatic)
# ---------------------------------------------------------------------------


class ConflictResolutionRepository:
    """Records human conflict resolutions per 14_knowledge_conflict_detection.md.

    The resolution flow (downgrade authority / set effective_until /
    acknowledge both) is a human decision gated by Document:reclassify.
    This repo persists the decision; the Document-table edit itself (if any)
    belongs to Character 3's document-pipeline.
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def record(
        self, payload: ConflictResolutionCreate, resolved_by: str
    ) -> ConflictResolution:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO conflict_resolutions
                    (equipment_id, claim_description, source_a_document_id,
                     source_b_document_id, resolution_kind, resolution_note,
                     resolved_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING *
                """,
                payload.equipment_id,
                payload.claim_description,
                payload.source_a_document_id,
                payload.source_b_document_id,
                payload.resolution_kind.value,
                payload.resolution_note,
                resolved_by,
            )
        return ConflictResolution(
            id=row["id"],
            equipment_id=row["equipment_id"],
            claim_description=row["claim_description"],
            source_a_document_id=row["source_a_document_id"],
            source_b_document_id=row["source_b_document_id"],
            resolution_kind=row["resolution_kind"],
            resolution_note=row["resolution_note"],
            resolved_by=row["resolved_by"],
            resolved_at=row["resolved_at"],
        )

    async def list_by_equipment(
        self, equipment_id: uuid.UUID
    ) -> list[ConflictResolution]:
        """Newest first — the Known-conflicts panel shows acknowledgments inline."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM conflict_resolutions
                WHERE equipment_id = $1
                ORDER BY resolved_at DESC
                """,
                equipment_id,
            )
        return [
            ConflictResolution(
                id=r["id"],
                equipment_id=r["equipment_id"],
                claim_description=r["claim_description"],
                source_a_document_id=r["source_a_document_id"],
                source_b_document_id=r["source_b_document_id"],
                resolution_kind=r["resolution_kind"],
                resolution_note=r["resolution_note"],
                resolved_by=r["resolved_by"],
                resolved_at=r["resolved_at"],
            )
            for r in rows
        ]
