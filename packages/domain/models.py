"""Canonical Model entity, shared across services (docs/domain/04_model_model.md).

Field names match docs/schemas/06_model_schema.md exactly. services/
import this instead of redefining the type (docs/15_CODEBASE_TARGET_STRUCTURE.md
dependency direction: services → packages, never the reverse).
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


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


class Model(BaseModel):
    """A registered inference model (docs/schemas/06_model_schema.md)."""

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
