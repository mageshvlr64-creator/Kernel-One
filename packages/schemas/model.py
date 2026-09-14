"""Model wire types (docs/schemas/06_model_schema.md) for services that
don't own the registry — mirrors packages/domain/models.py so a service
never imports another service's app code."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Provider(str, Enum):
    VLLM = "vllm"
    OLLAMA = "ollama"
    LLAMACPP = "llamacpp"


class Capability(str, Enum):
    CODING = "coding"
    VISION = "vision"
    TOOL_CALLING = "tool_calling"
    STRUCTURED_OUTPUT = "structured_output"
    OCR_ASSIST = "ocr_assist"


class DataClassification(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


_CLASSIFICATION_ORDER: dict[DataClassification, int] = {
    DataClassification.PUBLIC: 0,
    DataClassification.INTERNAL: 1,
    DataClassification.CONFIDENTIAL: 2,
    DataClassification.RESTRICTED: 3,
}


class Model(BaseModel):
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


class ModelSelectionRequest(BaseModel):
    """Body for POST /api/v1/router/select (docs/api/10_model_router_api.md)."""

    required_capabilities: list[Capability] = Field(default_factory=list)
    max_classification: Optional[DataClassification] = None
    preferred_provider: Optional[Provider] = None
    max_parameters_billions: Optional[float] = Field(default=None, ge=0)
    min_context_window: Optional[int] = Field(default=None, ge=1)


class ModelSelectionResponse(BaseModel):
    """{"data": {...}} payload for POST /api/v1/router/select."""

    model: Model
    fallback_chain: list[str] = Field(default_factory=list)
    reason: str = "best_match"
