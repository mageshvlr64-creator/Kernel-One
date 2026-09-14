"""
FastAPI application for the industrial-service.

Routes implemented:
  /assets          — list / search equipment (ui/23_asset_view.md /assets)
  /assets/:id      — equipment detail (ui/23_asset_view.md /assets/:equipmentId)
  /plants          — plant CRUD
  /plants/:id/units — unit management
  /units/:id/equipment — equipment under a unit
  /equipment/:id/...   — maintenance, inspections, incidents, governing docs
  /internal/resolve-tag    — entity resolution called by document-pipeline
  /internal/detect-conflicts — conflict detection called by evidence-service
  /internal/compare-documents — document diff endpoint

All routes respect the permission model (docs/reference/05_permission_matrix.md)
by checking a caller-supplied permission header.  In V1, real RBAC enforcement
lives in the API gateway (Character 1/5); this service trusts that the gateway
has already validated the JWT and forwards the caller's roles as a header.

Every mutating handler produces an AuditEvent via the audit-service API
(docs/features/17_audit/, docs/13_DEVELOPER_RULES.md rule 4).
"""

from __future__ import annotations

import os
import uuid
from contextlib import asynccontextmanager
from datetime import date
from typing import Annotated, Optional

import asyncpg
import httpx
from fastapi import Depends, FastAPI, HTTPException, Header, Query, status

from app.comparison import compare_findings, is_low_confidence
from app.conflict_detection import detect_conflicts, format_conflict_output
from app.database import (
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
from app.inspection_logic import (
    validate_calculation_framing,
    validate_sop_compliance_disclaimer,
)
from app.models import (
    ConflictRecord,
    DocumentDiff,
    Equipment,
    EquipmentCreate,
    EquipmentStatus,
    EquipmentUpdate,
    GoverningDocumentLinkCreate,
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
# App lifecycle
# ---------------------------------------------------------------------------

_pool: Optional[asyncpg.Pool] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _pool
    dsn = os.environ["DATABASE_URL"]
    _pool = await get_pool(dsn)
    await init_schema(_pool)
    yield
    await _pool.close()


app = FastAPI(
    title="Industrial Service",
    description=(
        "Character 4 — Industrial Intelligence. "
        "Owns assets, knowledge graph, change detection, conflict detection. "
        "See docs/industrial/ for the full specification."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Dependency injection
# ---------------------------------------------------------------------------


def get_db_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool not initialised")
    return _pool


def plant_repo(pool: asyncpg.Pool = Depends(get_db_pool)) -> PlantRepository:
    return PlantRepository(pool)


def unit_repo(pool: asyncpg.Pool = Depends(get_db_pool)) -> UnitRepository:
    return UnitRepository(pool)


def equipment_repo(pool: asyncpg.Pool = Depends(get_db_pool)) -> EquipmentRepository:
    return EquipmentRepository(pool)


def maintenance_repo(
    pool: asyncpg.Pool = Depends(get_db_pool),
) -> MaintenanceEventRepository:
    return MaintenanceEventRepository(pool)


def inspection_repo(
    pool: asyncpg.Pool = Depends(get_db_pool),
) -> InspectionRepository:
    return InspectionRepository(pool)


def incident_repo(
    pool: asyncpg.Pool = Depends(get_db_pool),
) -> IncidentRepository:
    return IncidentRepository(pool)


def graph_repo(
    pool: asyncpg.Pool = Depends(get_db_pool),
) -> KnowledgeGraphRepository:
    return KnowledgeGraphRepository(pool)


def entity_resolver(
    eq_repo: EquipmentRepository = Depends(equipment_repo),
    kg_repo: KnowledgeGraphRepository = Depends(graph_repo),
) -> EntityResolver:
    return EntityResolver(eq_repo, kg_repo)


# ---------------------------------------------------------------------------
# Audit helper
# ---------------------------------------------------------------------------


async def _emit_audit_event(
    action: str,
    entity_type: str,
    entity_id: str,
    actor: str,
    detail: Optional[str] = None,
) -> None:
    """Fire-and-forget POST to the audit-service.

    On failure we log but do NOT raise — failing to audit should not roll back
    the primary action (the audit service has its own retry/dead-letter
    mechanism per docs/features/17_audit/).
    """
    audit_url = os.environ.get("AUDIT_SERVICE_URL", "http://audit-service:8006")
    payload = {
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "actor": actor,
        "detail": detail,
    }
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post(f"{audit_url}/audit-events", json=payload)
    except Exception:
        # Documented failure mode: audit emission failure is logged, not raised.
        # See docs/failures/ for the named failure entry for this scenario.
        pass  # In production: log via OpenTelemetry


# ---------------------------------------------------------------------------
# Permission helper
# ---------------------------------------------------------------------------


def _require_permission(roles_header: Optional[str], required: str) -> None:
    """Check that the caller's roles header contains the required permission.

    V1 simplified: roles are passed as a comma-separated header by the API
    gateway after JWT validation.  The full permission matrix is in
    docs/reference/05_permission_matrix.md.

    Fails closed per docs/05_ARCHITECTURAL_PRINCIPLES.md principle 11:
    if the header is absent or the permission is missing, deny.
    """
    if not roles_header:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing roles header; {required} required.",
        )
    roles = {r.strip() for r in roles_header.split(",")}
    if required not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {required} required.",
        )


# ---------------------------------------------------------------------------
# Plants
# ---------------------------------------------------------------------------


@app.post("/plants", response_model=Plant, status_code=status.HTTP_201_CREATED)
async def create_plant(
    payload: PlantCreate,
    repo: PlantRepository = Depends(plant_repo),
    x_roles: Annotated[Optional[str], Header()] = None,
    x_actor: Annotated[Optional[str], Header()] = None,
):
    _require_permission(x_roles, "Equipment:write")
    plant = await repo.create(payload)
    await _emit_audit_event("create", "Plant", str(plant.id), x_actor or "unknown")
    return plant


@app.get("/plants/{plant_id}", response_model=Plant)
async def get_plant(
    plant_id: uuid.UUID,
    repo: PlantRepository = Depends(plant_repo),
    x_roles: Annotated[Optional[str], Header()] = None,
):
    _require_permission(x_roles, "Equipment:read")
    plant = await repo.get(plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    return plant


@app.get("/organizations/{org_id}/plants", response_model=list[Plant])
async def list_plants(
    org_id: uuid.UUID,
    repo: PlantRepository = Depends(plant_repo),
    x_roles: Annotated[Optional[str], Header()] = None,
):
    _require_permission(x_roles, "Equipment:read")
    return await repo.list_by_org(org_id)


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------


@app.post("/units", response_model=Unit, status_code=status.HTTP_201_CREATED)
async def create_unit(
    payload: UnitCreate,
    repo: UnitRepository = Depends(unit_repo),
    x_roles: Annotated[Optional[str], Header()] = None,
    x_actor: Annotated[Optional[str], Header()] = None,
):
    _require_permission(x_roles, "Equipment:write")
    unit = await repo.create(payload)
    await _emit_audit_event("create", "Unit", str(unit.id), x_actor or "unknown")
    return unit


@app.get("/units/{unit_id}", response_model=Unit)
async def get_unit(
    unit_id: uuid.UUID,
    repo: UnitRepository = Depends(unit_repo),
    x_roles: Annotated[Optional[str], Header()] = None,
):
    _require_permission(x_roles, "Equipment:read")
    unit = await repo.get(unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    return unit


@app.get("/plants/{plant_id}/units", response_model=list[Unit])
async def list_units(
    plant_id: uuid.UUID,
    repo: UnitRepository = Depends(unit_repo),
    x_roles: Annotated[Optional[str], Header()] = None,
):
    _require_permission(x_roles, "Equipment:read")
    return await repo.list_by_plant(plant_id)


# ---------------------------------------------------------------------------
# Equipment — list / search (Asset list view, docs/ui/23_asset_view.md /assets)
# ---------------------------------------------------------------------------


@app.get("/assets", response_model=list[Equipment])
async def list_assets(
    organization_id: uuid.UUID,
    tag_number: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    equipment_status: Optional[EquipmentStatus] = Query(None, alias="status"),
    repo: EquipmentRepository = Depends(equipment_repo),
    x_roles: Annotated[Optional[str], Header()] = None,
):
    """Search all equipment visible to the organization.

    Implements the list view from docs/ui/23_asset_view.md:
    Filter by tag number, name, status.
    """
    _require_permission(x_roles, "Equipment:read")
    return await repo.search(
        organization_id=organization_id,
        tag_number=tag_number,
        name_query=name,
        status=equipment_status,
    )


# ---------------------------------------------------------------------------
# Equipment — CRUD
# ---------------------------------------------------------------------------


@app.post(
    "/units/{unit_id}/equipment",
    response_model=Equipment,
    status_code=status.HTTP_201_CREATED,
)
async def create_equipment(
    unit_id: uuid.UUID,
    payload: EquipmentCreate,
    repo: EquipmentRepository = Depends(equipment_repo),
    x_roles: Annotated[Optional[str], Header()] = None,
    x_actor: Annotated[Optional[str], Header()] = None,
):
    _require_permission(x_roles, "Equipment:write")
    if payload.unit_id != unit_id:
        raise HTTPException(
            status_code=400, detail="unit_id in path must match unit_id in body"
        )
    equipment = await repo.create(payload)
    await _emit_audit_event(
        "create", "Equipment", str(equipment.id), x_actor or "unknown"
    )
    return equipment


@app.get("/assets/{equipment_id}", response_model=Equipment)
async def get_equipment(
    equipment_id: uuid.UUID,
    repo: EquipmentRepository = Depends(equipment_repo),
    x_roles: Annotated[Optional[str], Header()] = None,
):
    """Equipment detail view (docs/ui/23_asset_view.md /assets/:equipmentId header)."""
    _require_permission(x_roles, "Equipment:read")
    equipment = await repo.get(equipment_id)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return equipment


@app.patch("/assets/{equipment_id}", response_model=Equipment)
async def update_equipment(
    equipment_id: uuid.UUID,
    payload: EquipmentUpdate,
    repo: EquipmentRepository = Depends(equipment_repo),
    x_roles: Annotated[Optional[str], Header()] = None,
    x_actor: Annotated[Optional[str], Header()] = None,
):
    """Update equipment fields — primarily used to update status.

    Status changes are gated by Equipment:write per docs/domain/20_asset_model.md.
    Status is NOT automatically derived from inspection findings (principle 6).
    """
    _require_permission(x_roles, "Equipment:write")
    equipment = await repo.update(equipment_id, payload)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    await _emit_audit_event(
        "update",
        "Equipment",
        str(equipment_id),
        x_actor or "unknown",
        detail=f"status={payload.status.value if payload.status else 'unchanged'}",
    )
    return equipment


@app.delete("/assets/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_equipment(
    equipment_id: uuid.UUID,
    repo: EquipmentRepository = Depends(equipment_repo),
    x_roles: Annotated[Optional[str], Header()] = None,
    x_actor: Annotated[Optional[str], Header()] = None,
):
    _require_permission(x_roles, "Equipment:write")
    deleted = await repo.soft_delete(equipment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Equipment not found")
    await _emit_audit_event(
        "delete", "Equipment", str(equipment_id), x_actor or "unknown"
    )


# ---------------------------------------------------------------------------
# Maintenance events
# ---------------------------------------------------------------------------


@app.post(
    "/assets/{equipment_id}/maintenance-events",
    response_model=MaintenanceEvent,
    status_code=status.HTTP_201_CREATED,
)
async def create_maintenance_event(
    equipment_id: uuid.UUID,
    payload: MaintenanceEventCreate,
    repo: MaintenanceEventRepository = Depends(maintenance_repo),
    eq_repo: EquipmentRepository = Depends(equipment_repo),
    x_roles: Annotated[Optional[str], Header()] = None,
    x_actor: Annotated[Optional[str], Header()] = None,
):
    _require_permission(x_roles, "Equipment:write")
    if not await eq_repo.get(equipment_id):
        raise HTTPException(status_code=404, detail="Equipment not found")
    if payload.equipment_id != equipment_id:
        raise HTTPException(
            status_code=400, detail="equipment_id in path must match body"
        )
    event = await repo.create(payload)
    await _emit_audit_event(
        "create", "MaintenanceEvent", str(event.id), x_actor or "unknown"
    )
    return event


@app.get(
    "/assets/{equipment_id}/maintenance-events",
    response_model=list[MaintenanceEvent],
)
async def list_maintenance_events(
    equipment_id: uuid.UUID,
    repo: MaintenanceEventRepository = Depends(maintenance_repo),
    x_roles: Annotated[Optional[str], Header()] = None,
):
    _require_permission(x_roles, "Equipment:read")
    return await repo.list_by_equipment(equipment_id)


# ---------------------------------------------------------------------------
# Inspections
# ---------------------------------------------------------------------------


@app.post(
    "/assets/{equipment_id}/inspections",
    response_model=Inspection,
    status_code=status.HTTP_201_CREATED,
)
async def create_inspection(
    equipment_id: uuid.UUID,
    payload: InspectionCreate,
    repo: InspectionRepository = Depends(inspection_repo),
    eq_repo: EquipmentRepository = Depends(equipment_repo),
    x_roles: Annotated[Optional[str], Header()] = None,
    x_actor: Annotated[Optional[str], Header()] = None,
):
    _require_permission(x_roles, "Equipment:write")
    if not await eq_repo.get(equipment_id):
        raise HTTPException(status_code=404, detail="Equipment not found")
    if payload.equipment_id != equipment_id:
        raise HTTPException(
            status_code=400, detail="equipment_id in path must match body"
        )
    inspection = await repo.create(payload)
    await _emit_audit_event(
        "create", "Inspection", str(inspection.id), x_actor or "unknown"
    )
    return inspection


@app.get("/assets/{equipment_id}/inspections", response_model=list[Inspection])
async def list_inspections(
    equipment_id: uuid.UUID,
    repo: InspectionRepository = Depends(inspection_repo),
    x_roles: Annotated[Optional[str], Header()] = None,
):
    _require_permission(x_roles, "Equipment:read")
    return await repo.list_by_equipment(equipment_id)


# ---------------------------------------------------------------------------
# Incidents
# ---------------------------------------------------------------------------


@app.post(
    "/assets/{equipment_id}/incidents",
    response_model=Incident,
    status_code=status.HTTP_201_CREATED,
)
async def create_incident(
    equipment_id: uuid.UUID,
    payload: IncidentCreate,
    repo: IncidentRepository = Depends(incident_repo),
    eq_repo: EquipmentRepository = Depends(equipment_repo),
    x_roles: Annotated[Optional[str], Header()] = None,
    x_actor: Annotated[Optional[str], Header()] = None,
):
    _require_permission(x_roles, "Equipment:write")
    if not await eq_repo.get(equipment_id):
        raise HTTPException(status_code=404, detail="Equipment not found")
    if payload.equipment_id != equipment_id:
        raise HTTPException(
            status_code=400, detail="equipment_id in path must match body"
        )
    incident = await repo.create(payload)
    await _emit_audit_event(
        "create", "Incident", str(incident.id), x_actor or "unknown"
    )
    return incident


@app.get("/assets/{equipment_id}/incidents", response_model=list[Incident])
async def list_incidents(
    equipment_id: uuid.UUID,
    repo: IncidentRepository = Depends(incident_repo),
    x_roles: Annotated[Optional[str], Header()] = None,
):
    _require_permission(x_roles, "Equipment:read")
    return await repo.list_by_equipment(equipment_id)


# ---------------------------------------------------------------------------
# Governing documents (knowledge graph edges)
# ---------------------------------------------------------------------------


@app.post(
    "/assets/{equipment_id}/governing-documents",
    status_code=status.HTTP_201_CREATED,
)
async def add_governing_document(
    equipment_id: uuid.UUID,
    payload: GoverningDocumentLinkCreate,
    repo: KnowledgeGraphRepository = Depends(graph_repo),
    eq_repo: EquipmentRepository = Depends(equipment_repo),
    x_roles: Annotated[Optional[str], Header()] = None,
    x_actor: Annotated[Optional[str], Header()] = None,
):
    """Add a governed_by edge from Equipment to a Document.

    Gated by Equipment:write per docs/ui/23_asset_view.md actions section.
    The human-confirmation flow for case-2 entity resolution is handled
    by the caller before calling this endpoint.
    """
    _require_permission(x_roles, "Equipment:write")
    if not await eq_repo.get(equipment_id):
        raise HTTPException(status_code=404, detail="Equipment not found")
    link = await repo.add_governing_document(
        equipment_id=equipment_id,
        document_id=payload.document_id,
        relationship_note=payload.relationship_note,
    )
    await _emit_audit_event(
        "add_governing_document",
        "Equipment",
        str(equipment_id),
        x_actor or "unknown",
        detail=f"document_id={payload.document_id}",
    )
    return link


@app.delete(
    "/assets/{equipment_id}/governing-documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_governing_document(
    equipment_id: uuid.UUID,
    document_id: uuid.UUID,
    repo: KnowledgeGraphRepository = Depends(graph_repo),
    x_roles: Annotated[Optional[str], Header()] = None,
    x_actor: Annotated[Optional[str], Header()] = None,
):
    _require_permission(x_roles, "Equipment:write")
    removed = await repo.remove_governing_document(equipment_id, document_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Governing document link not found")
    await _emit_audit_event(
        "remove_governing_document",
        "Equipment",
        str(equipment_id),
        x_actor or "unknown",
        detail=f"document_id={document_id}",
    )


@app.get("/assets/{equipment_id}/governing-documents")
async def get_governing_documents(
    equipment_id: uuid.UUID,
    repo: KnowledgeGraphRepository = Depends(graph_repo),
    x_roles: Annotated[Optional[str], Header()] = None,
):
    _require_permission(x_roles, "Equipment:read")
    return await repo.get_governing_documents(equipment_id)


# ---------------------------------------------------------------------------
# Internal endpoints — called by other services, not directly by the UI
# ---------------------------------------------------------------------------


class ResolveTagRequest(PlantCreate):
    """Re-using PlantCreate is wrong here — use a proper schema."""
    pass


from pydantic import BaseModel as _BaseModel


class ResolveTagRequest(_BaseModel):
    tag_number: str
    within_unit_id: uuid.UUID
    plant_id: uuid.UUID


@app.post("/internal/resolve-tag")
async def resolve_tag(
    payload: ResolveTagRequest,
    resolver: EntityResolver = Depends(entity_resolver),
):
    """Resolve an equipment tag extracted from a document.

    Called by services/document-pipeline/ (Character 3) when a new document
    is ingested and equipment tags are found.

    Returns an EntityResolutionResult.  The document-pipeline is responsible
    for surfacing case-2 results for human confirmation before persisting any
    governed_by edge.
    """
    return await resolver.resolve(
        tag_number=payload.tag_number,
        within_unit_id=payload.within_unit_id,
        plant_id=payload.plant_id,
    )


class ConfirmLinkRequest(_BaseModel):
    equipment_id: uuid.UUID
    document_id: uuid.UUID
    relationship_note: Optional[str] = None


@app.post("/internal/confirm-link", status_code=status.HTTP_201_CREATED)
async def confirm_link(
    payload: ConfirmLinkRequest,
    resolver: EntityResolver = Depends(entity_resolver),
    x_actor: Annotated[Optional[str], Header()] = None,
    x_roles: Annotated[Optional[str], Header()] = None,
):
    """Persist a governed_by edge after human confirmation.

    Handles both case-1 auto-links (called programmatically) and case-2
    human-confirmed links (called after the human approves the ambiguous match).
    """
    _require_permission(x_roles, "Equipment:write")
    await resolver.confirm_and_link(
        equipment_id=payload.equipment_id,
        document_id=payload.document_id,
        relationship_note=payload.relationship_note,
    )
    await _emit_audit_event(
        "confirm_governing_link",
        "Equipment",
        str(payload.equipment_id),
        x_actor or "unknown",
        detail=f"document_id={payload.document_id}",
    )
    return {"status": "linked"}


class DetectConflictsRequest(_BaseModel):
    equipment_id: uuid.UUID
    claims: list[dict]


@app.post("/internal/detect-conflicts", response_model=list[ConflictRecord])
async def detect_conflicts_endpoint(
    payload: DetectConflictsRequest,
):
    """Run conflict detection for one piece of equipment.

    Called by services/evidence-service/ (Character 3) at retrieval time or
    when a new document is ingested (background check case per
    docs/industrial/14_knowledge_conflict_detection.md).

    The caller is responsible for pre-fetching the relevant claims/Evidence rows.
    This endpoint applies the deterministic detection logic and returns
    ConflictRecord objects — it never auto-resolves anything.
    """
    return detect_conflicts(
        equipment_id=payload.equipment_id,
        claims=payload.claims,
    )


class CompareDocumentsRequest(_BaseModel):
    document_a_id: uuid.UUID
    document_b_id: uuid.UUID
    findings_a: list[dict]
    findings_b: list[dict]


@app.post("/internal/compare-documents", response_model=DocumentDiff)
async def compare_documents_endpoint(
    payload: CompareDocumentsRequest,
):
    """Produce a structured diff between two sets of findings.

    Called by the agent kernel (Character 2) when executing a document
    comparison workflow (docs/workflows/06_document_comparison.md).

    The caller is responsible for retrieving the findings from each document
    independently — this endpoint only applies the deterministic classification.
    """
    return compare_findings(
        document_a_id=payload.document_a_id,
        document_b_id=payload.document_b_id,
        findings_a=payload.findings_a,
        findings_b=payload.findings_b,
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "industrial-service"}
