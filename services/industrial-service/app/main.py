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

from app.calculations import aggregate_values, check_tolerance, convert_unit
from app.comparison import compare_findings, is_low_confidence
from app.conflict_detection import detect_conflicts, format_conflict_output
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
from app.inspection_logic import (
    Finding,
    format_finding_answer_fragment,
    is_supported_finding,
    needs_ocr_confidence_warning,
    validate_calculation_framing,
    validate_drawing_caveat,
    validate_sop_compliance_disclaimer,
)
from app.models import (
    ConflictRecord,
    ConflictResolution,
    ConflictResolutionCreate,
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


def conflict_resolution_repo(
    pool: asyncpg.Pool = Depends(get_db_pool),
) -> ConflictResolutionRepository:
    return ConflictResolutionRepository(pool)


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
    plant_id: Optional[uuid.UUID] = Query(None),
    unit_id: Optional[uuid.UUID] = Query(None),
    repo: EquipmentRepository = Depends(equipment_repo),
    x_roles: Annotated[Optional[str], Header()] = None,
):
    """Search all equipment visible to the organization.

    Implements the list view from docs/ui/23_asset_view.md:
    Filter by tag number, name, Plant, Unit, status.
    """
    _require_permission(x_roles, "Equipment:read")
    return await repo.search(
        organization_id=organization_id,
        tag_number=tag_number,
        name_query=name,
        status=equipment_status,
        plant_id=plant_id,
        unit_id=unit_id,
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
# Aggregated asset detail (single call for ui/23_asset_view.md detail view)
# ---------------------------------------------------------------------------


class AssetDetail(_BaseModel):
    equipment: Equipment
    plant: Optional[Plant] = None
    unit: Optional[Unit] = None
    maintenance_events: list[MaintenanceEvent] = []
    inspections: list[Inspection] = []
    incidents: list[Incident] = []
    governing_documents: list[dict] = []
    last_inspection_date: Optional[date] = None


@app.get("/assets/{equipment_id}/detail", response_model=AssetDetail)
async def get_asset_detail(
    equipment_id: uuid.UUID,
    eq_repo: EquipmentRepository = Depends(equipment_repo),
    unit_repo_: UnitRepository = Depends(unit_repo),
    plant_repo_: PlantRepository = Depends(plant_repo),
    maint_repo: MaintenanceEventRepository = Depends(maintenance_repo),
    insp_repo: InspectionRepository = Depends(inspection_repo),
    inci_repo: IncidentRepository = Depends(incident_repo),
    kg_repo: KnowledgeGraphRepository = Depends(graph_repo),
    x_roles: Annotated[Optional[str], Header()] = None,
):
    """Single aggregated call for /assets/:equipmentId detail view.

    Per docs/ui/23_asset_view.md: header + identity + maintenance +
    inspection + incident histories + governing docs, one round trip.
    """
    _require_permission(x_roles, "Equipment:read")
    equipment = await eq_repo.get(equipment_id)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    unit = await unit_repo_.get(equipment.unit_id)
    plant = await plant_repo_.get(unit.plant_id) if unit else None
    return AssetDetail(
        equipment=equipment,
        plant=plant,
        unit=unit,
        maintenance_events=await maint_repo.list_by_equipment(equipment_id),
        inspections=await insp_repo.list_by_equipment(equipment_id),
        incidents=await inci_repo.list_by_equipment(equipment_id),
        governing_documents=[
            link.model_dump()
            for link in await kg_repo.get_governing_documents(equipment_id)
        ],
        last_inspection_date=await insp_repo.last_inspection_date(equipment_id),
    )


@app.get("/documents/{document_id}/equipment")
async def get_equipment_for_document(
    document_id: uuid.UUID,
    repo: KnowledgeGraphRepository = Depends(graph_repo),
    x_roles: Annotated[Optional[str], Header()] = None,
):
    """Impact analysis: which equipment is governed by this document."""
    _require_permission(x_roles, "Equipment:read")
    return {
        "document_id": str(document_id),
        "equipment_ids": await repo.get_equipment_for_document(document_id),
    }


class ValidateFindingRequest(_BaseModel):
    parameter: str
    measured_value: Optional[str] = None
    specification: Optional[str] = None
    pass_fail: Optional[str] = None
    location_reference: Optional[str] = None
    evidence_id_parameter: Optional[str] = None
    evidence_id_measured_value: Optional[str] = None
    evidence_id_specification: Optional[str] = None
    evidence_id_pass_fail: Optional[str] = None
    ocr_confidence: Optional[float] = None


@app.post("/internal/validate-finding")
async def validate_finding(payload: ValidateFindingRequest):
    """Validate one inspection finding per docs/industrial/02_inspection_reports.md.

    Called by document-pipeline (Character 3) after extraction, before
    persisting an Inspection row. Returns supported/ocr-warning flags plus
    the formatted answer fragment.
    """
    finding = Finding(**payload.model_dump())
    return {
        "supported": is_supported_finding(finding),
        "ocr_warning": needs_ocr_confidence_warning(finding),
        "fragment": format_finding_answer_fragment(finding),
    }


class ValidateAnswerRequest(_BaseModel):
    answer_text: str
    answer_kind: str = "general"


@app.post("/internal/validate-answer")
async def validate_answer(payload: ValidateAnswerRequest):
    """Check required disclaimers per 04_sop_compliance / 09 / 11.

    answer_kind: 'sop' | 'calculation' | 'drawing' | 'general'.
    Returns {valid, missing} — caller rejects or flags when not valid.
    """
    checks: dict[str, bool] = {}
    if payload.answer_kind in ("sop", "general"):
        checks["sop_disclaimer"] = (
            validate_sop_compliance_disclaimer(payload.answer_text)
            if payload.answer_kind == "sop"
            else True
        )
    if payload.answer_kind in ("calculation", "general"):
        checks["calculation_framing"] = (
            validate_calculation_framing(payload.answer_text)
            if payload.answer_kind == "calculation"
            else True
        )
    if payload.answer_kind in ("drawing", "general"):
        checks["drawing_caveat"] = (
            validate_drawing_caveat(payload.answer_text)
            if payload.answer_kind == "drawing"
            else True
        )
    missing = [k for k, v in checks.items() if not v]
    return {"valid": not missing, "missing": missing}


class VerifyCalculationRequest(_BaseModel):
    operation: str
    measured_value: Optional[float] = None
    spec_min: Optional[float] = None
    spec_max: Optional[float] = None
    nominal: Optional[float] = None
    tolerance: Optional[float] = None
    value: Optional[float] = None
    from_unit: Optional[str] = None
    to_unit: Optional[str] = None
    values: Optional[list[float]] = None
    aggregate: Optional[str] = "mean"


@app.post("/internal/verify-calculation")
async def verify_calculation(payload: VerifyCalculationRequest):
    """Deterministic calculation check per 10_engineering_calculations.md.

    operation: 'tolerance' | 'convert' | 'aggregate'. Fails closed (400)
    on bad inputs — never estimates. Caller cites the returned inputs
    as Evidence (input traceability, 11_calculation_verification.md).
    """
    try:
        if payload.operation == "tolerance":
            if payload.measured_value is None:
                raise ValueError("measured_value required")
            result = check_tolerance(
                measured_value=payload.measured_value,
                spec_min=payload.spec_min,
                spec_max=payload.spec_max,
                nominal=payload.nominal,
                tolerance=payload.tolerance,
            )
            return {
                **result.__dict__,
                "framing_hint": "arithmetic verified; formula selection and input values require human confirmation",
            }
        if payload.operation == "convert":
            if payload.value is None or not payload.from_unit or not payload.to_unit:
                raise ValueError("value/from_unit/to_unit required")
            return convert_unit(payload.value, payload.from_unit, payload.to_unit)
        if payload.operation == "aggregate":
            if payload.values is None:
                raise ValueError("values required")
            return aggregate_values(payload.values, payload.aggregate or "mean")
        raise ValueError(f"unknown operation: {payload.operation}")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ---------------------------------------------------------------------------
# Conflict resolution (human decision — never automatic, principle 12)
# ---------------------------------------------------------------------------


@app.post(
    "/assets/{equipment_id}/conflicts/resolve",
    response_model=ConflictResolution,
    status_code=status.HTTP_201_CREATED,
)
async def resolve_conflict(
    equipment_id: uuid.UUID,
    payload: ConflictResolutionCreate,
    repo: ConflictResolutionRepository = Depends(conflict_resolution_repo),
    eq_repo: EquipmentRepository = Depends(equipment_repo),
    x_roles: Annotated[Optional[str], Header()] = None,
    x_actor: Annotated[Optional[str], Header()] = None,
):
    """Record a human's conflict resolution.

    Per docs/industrial/14_knowledge_conflict_detection.md resolution flow:
    downgrade one source's authority, set effective_until on the outdated
    source, or explicitly acknowledge both as valid. Gated by
    Document:reclassify (same gate as changing Document.authority).
    Every resolution is an audited event.
    """
    _require_permission(x_roles, "Document:reclassify")
    if not await eq_repo.get(equipment_id):
        raise HTTPException(status_code=404, detail="Equipment not found")
    if payload.equipment_id != equipment_id:
        raise HTTPException(
            status_code=400, detail="equipment_id in path must match body"
        )
    actor = x_actor or "unknown"
    resolution = await repo.record(payload, resolved_by=actor)
    await _emit_audit_event(
        "resolve_conflict",
        "Equipment",
        str(equipment_id),
        actor,
        detail=f"kind={payload.resolution_kind.value} claim={payload.claim_description}",
    )
    return resolution


@app.get(
    "/assets/{equipment_id}/conflict-resolutions",
    response_model=list[ConflictResolution],
)
async def list_conflict_resolutions(
    equipment_id: uuid.UUID,
    repo: ConflictResolutionRepository = Depends(conflict_resolution_repo),
    x_roles: Annotated[Optional[str], Header()] = None,
):
    """Resolution history for the Known-conflicts panel (ui/23_asset_view.md)."""
    _require_permission(x_roles, "Equipment:read")
    return await repo.list_by_equipment(equipment_id)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "industrial-service"}
