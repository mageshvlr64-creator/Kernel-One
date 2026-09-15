"""Domain types for the Model Router service.

Matches docs/schemas/06_model_schema.md field-for-field.
Every type here is the single source of truth for the model-router's wire/storage contract;
other services import these from packages/schemas/ once that package is scaffolded.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Provider(str, Enum):
    """Supported inference providers."""
    VLLM = "vllm"
    OLLAMA = "ollama"
    LLAMACPP = "llamacpp"


class Capability(str, Enum):
    """Model capability tags."""
    CODING = "coding"
    VISION = "vision"
    TOOL_CALLING = "tool_calling"
    STRUCTURED_OUTPUT = "structured_output"
    OCR_ASSIST = "ocr_assist"


class DataClassification(str, Enum):
    """Data classification levels (highest clearance a model may serve)."""
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


# Ordered for comparison — index position = clearance level.
_CLASSIFICATION_ORDER: dict[DataClassification, int] = {
    DataClassification.PUBLIC: 0,
    DataClassification.INTERNAL: 1,
    DataClassification.CONFIDENTIAL: 2,
    DataClassification.RESTRICTED: 3,
}


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


# ---------------------------------------------------------------------------
# Core entity — matches schemas/06_model_schema.md exactly
# ---------------------------------------------------------------------------

class Model(BaseModel):
    """A registered inference model.

    Field names and types mirror the JSON Schema in docs/schemas/06_model_schema.md.
    """

    id: str
    display_name: Optional[str] = None
    provider: Provider
    total_parameters_billions: float = Field(ge=0)
    active_parameters_billions: Optional[float] = Field(default=None, ge=0)
    quantization: Optional[str] = None
    context_window: int = Field(ge=1)
    capabilities: list[Capability] = Field(default_factory=list)
    max_classification: DataClassification
    is_available: bool = True

    @property
    def display(self) -> str:
        return self.display_name or self.id


# ---------------------------------------------------------------------------
# Selection request / response
# ---------------------------------------------------------------------------

class ModelSelectionRequest(BaseModel):
    """Request body for the model selection endpoint.

    The router picks the best available model that satisfies all filters.
    """

    required_capabilities: list[Capability] = Field(default_factory=list)
    max_classification: Optional[DataClassification] = None
    preferred_provider: Optional[Provider] = None
    max_parameters_billions: Optional[float] = Field(default=None, ge=0)
    min_context_window: Optional[int] = Field(default=None, ge=1)


class ModelSelectionResponse(BaseModel):
    """Returned when a model is successfully selected."""

    model: Model
    fallback_chain: list[str] = Field(default_factory=list)
    reason: str = "best_match"


class ModelHealth(BaseModel):
    """Health status for a single model/provider."""

    model_id: str
    provider: Provider
    is_healthy: bool
    latency_ms: Optional[float] = None
    last_check: Optional[str] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Audit event payload (emitted on every model-selection call)
# ---------------------------------------------------------------------------

class AuditEvent(BaseModel):
    """Lightweight audit event for model-router operations.

    Full audit schema lives in docs/schemas/15_audit_event_schema.md; this is
    the subset the model-router emits internally.
    """

    event_type: str = "model_selection"
    actor_id: Optional[str] = None
    model_id: Optional[str] = None
    provider: Optional[Provider] = None
    classification: Optional[DataClassification] = None
    result: str = "success"  # "success" | "error" | "fallback"
    error_code: Optional[str] = None
    details: Optional[str] = None
