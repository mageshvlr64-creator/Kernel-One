"""Shared wire types generated from docs/schemas/ blocks.

services/ import from here — never redefine envelope or entity shapes
(docs/15_CODEBASE_TARGET_STRUCTURE.md). Character 1 (Foundation &
Inference) owns this package per TEAM.md.
"""

from .envelope import ApiErrorEnvelope, ApiSuccessEnvelope
from .model import (
    Capability,
    DataClassification,
    Model,
    Provider,
    _CLASSIFICATION_ORDER,
)
from .selection import (
    ModelSelectionRequest,
    ModelSelectionResponse,
)

__all__ = [
    "ApiErrorEnvelope",
    "ApiSuccessEnvelope",
    "Capability",
    "DataClassification",
    "Model",
    "ModelSelectionRequest",
    "ModelSelectionResponse",
    "Provider",
    "_CLASSIFICATION_ORDER",
]
