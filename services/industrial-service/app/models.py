"""
Domain types for the industrial-service asset model.

Canonical field-level source: docs/domain/20_asset_model.md
All enums and field constraints here must stay consistent with that file.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class EquipmentStatus(str, Enum):
    """Operator-set status for a piece of equipment.

    Status is NOT automatically derived from inspection findings in V1.
    A human must confirm status changes — see docs/05_ARCHITECTURAL_PRINCIPLES.md
    principle 6 and docs/domain/20_asset_model.md.
    """

    operational = "operational"
    degraded = "degraded"
    down = "down"
    decommissioned = "decommissioned"


class FindingSeverity(str, Enum):
    """Severity levels used by Inspection and Incident rows."""

    informational = "informational"
    minor = "minor"
    major = "major"
    critical = "critical"


# ---------------------------------------------------------------------------
# Plant
# ---------------------------------------------------------------------------


class PlantBase(BaseModel):
    name: str = Field(..., description="e.g. 'Vadodara Refinery'")
    location: Optional[str] = Field(
        None, description="Free text; not geocoded in V1"
    )


class PlantCreate(PlantBase):
    organization_id: uuid.UUID


class Plant(PlantBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Unit
# ---------------------------------------------------------------------------


class UnitBase(BaseModel):
    name: str = Field(..., description="e.g. 'Crude Distillation Unit 2'")
    unit_type: Optional[str] = Field(
        None,
        description="Free text classification, e.g. 'distillation', 'utilities'",
    )


class UnitCreate(UnitBase):
    plant_id: uuid.UUID


class Unit(UnitBase):
    id: uuid.UUID
    plant_id: uuid.UUID
    created_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Equipment
# ---------------------------------------------------------------------------


class EquipmentBase(BaseModel):
    tag_number: str = Field(
        ...,
        description=(
            "Unique within unit_id; the physical/P&ID tag, e.g. 'P-204'. "
            "Used for entity resolution during document ingestion."
        ),
    )
    name: str = Field(..., description="e.g. 'Feed Pump P-204'")
    equipment_type: Optional[str] = Field(
        None,
        description="Free text, e.g. 'centrifugal pump', 'pressure vessel'",
    )
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    status: EquipmentStatus = EquipmentStatus.operational
    commissioned_at: Optional[date] = None


class EquipmentCreate(EquipmentBase):
    unit_id: uuid.UUID


class EquipmentUpdate(BaseModel):
    """Fields the caller may update.  Status changes are the primary use-case
    (gated by Equipment:write per docs/reference/05_permission_matrix.md)."""

    status: Optional[EquipmentStatus] = None
    equipment_type: Optional[str] = None
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    commissioned_at: Optional[date] = None


class Equipment(EquipmentBase):
    id: uuid.UUID
    unit_id: uuid.UUID
    created_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# MaintenanceEvent
# ---------------------------------------------------------------------------


class MaintenanceEventBase(BaseModel):
    event_type: Optional[str] = Field(
        None, description="Free text, e.g. 'seal replacement', 'scheduled service'"
    )
    performed_at: Optional[date] = None
    notes: Optional[str] = None


class MaintenanceEventCreate(MaintenanceEventBase):
    equipment_id: uuid.UUID
    source_document_id: Optional[uuid.UUID] = Field(
        None,
        description=(
            "The maintenance record Document this event was extracted from. "
            "See docs/industrial/03_maintenance_records.md."
        ),
    )


class MaintenanceEvent(MaintenanceEventBase):
    id: uuid.UUID
    equipment_id: uuid.UUID
    source_document_id: Optional[uuid.UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Inspection
# ---------------------------------------------------------------------------


class InspectionBase(BaseModel):
    inspected_at: Optional[date] = None
    finding_summary: Optional[str] = None
    severity: Optional[FindingSeverity] = None


class InspectionCreate(InspectionBase):
    equipment_id: uuid.UUID
    source_document_id: Optional[uuid.UUID] = Field(
        None,
        description=(
            "The inspection report Document this row was extracted from. "
            "See docs/industrial/02_inspection_reports.md."
        ),
    )


class Inspection(InspectionBase):
    id: uuid.UUID
    equipment_id: uuid.UUID
    source_document_id: Optional[uuid.UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Incident
# ---------------------------------------------------------------------------


class IncidentBase(BaseModel):
    occurred_at: Optional[date] = None
    description: Optional[str] = None
    severity: Optional[FindingSeverity] = None


class IncidentCreate(IncidentBase):
    equipment_id: uuid.UUID
    source_document_id: Optional[uuid.UUID] = None


class Incident(IncidentBase):
    id: uuid.UUID
    equipment_id: uuid.UUID
    source_document_id: Optional[uuid.UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Knowledge-graph helpers
# ---------------------------------------------------------------------------


class GoverningDocumentLink(BaseModel):
    """Represents one row in equipment_governing_documents.

    Many-to-many: one pump can be governed by multiple SOPs, and one SOP can
    govern multiple pumps.  See docs/industrial/13_asset_knowledge_graph.md.
    """

    equipment_id: uuid.UUID
    document_id: uuid.UUID
    relationship_note: Optional[str] = Field(
        None,
        description=(
            "Human-readable label, e.g. 'operating procedure', "
            "'lockout-tagout procedure'"
        ),
    )


class GoverningDocumentLinkCreate(BaseModel):
    document_id: uuid.UUID
    relationship_note: Optional[str] = None


# ---------------------------------------------------------------------------
# Conflict detection output
# ---------------------------------------------------------------------------


class ConflictRecord(BaseModel):
    """Structured conflict record produced by docs/industrial/14_knowledge_conflict_detection.md.

    This is NOT a new table — it's built from Evidence.verification_status='contradicted'
    pairs and surfaced to the caller.  The caller (API/UI) renders it per ui/23_asset_view.md.
    """

    equipment_id: uuid.UUID
    claim_description: str = Field(
        ...,
        description=(
            "Human-readable description of the parameter in dispute, "
            "e.g. 'Filter replacement interval for Equipment P-204'"
        ),
    )
    source_a_document_id: uuid.UUID
    source_a_document_name: str
    source_a_authority: str
    source_a_effective_from: Optional[date]
    source_a_claim: str

    source_b_document_id: uuid.UUID
    source_b_document_name: str
    source_b_authority: str
    source_b_effective_from: Optional[date]
    source_b_claim: str

    status: str = "unresolved"
    resolution_note: Optional[str] = None


# ---------------------------------------------------------------------------
# Document comparison / change detection output
# ---------------------------------------------------------------------------


class DiffEntry(BaseModel):
    """One entry in a structured document diff.

    See docs/industrial/05_document_comparison.md and 06_change_detection.md.
    """

    change_type: str = Field(
        ..., description="One of 'added', 'removed', 'changed'"
    )
    parameter: str
    location_reference: Optional[str] = None
    value_in_document_a: Optional[str] = None
    value_in_document_b: Optional[str] = None
    # Confidence inherited from the underlying Evidence retrieval
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description=(
            "Confidence score from Evidence rows; low-confidence entries "
            "are flagged distinctly per docs/industrial/06_change_detection.md."
        ),
    )
    evidence_id_a: Optional[uuid.UUID] = None
    evidence_id_b: Optional[uuid.UUID] = None


class DocumentDiff(BaseModel):
    document_a_id: uuid.UUID
    document_b_id: uuid.UUID
    added: list[DiffEntry] = []
    removed: list[DiffEntry] = []
    changed: list[DiffEntry] = []


# ---------------------------------------------------------------------------
# Entity-resolution result (used internally during document ingestion)
# ---------------------------------------------------------------------------


class EntityResolutionResult(BaseModel):
    """Result of matching a document's equipment tag to an Equipment row.

    Per docs/industrial/13_asset_knowledge_graph.md entity resolution section.
    """

    tag_number: str
    confidence: str = Field(
        ...,
        description=(
            "One of 'exact_same_unit' (auto-linked), "
            "'exact_other_unit' (flagged for human), 'no_match'"
        ),
    )
    matched_equipment_id: Optional[uuid.UUID] = None
    matched_unit_id: Optional[uuid.UUID] = None
    requires_human_confirmation: bool = False
    reason: str = ""
