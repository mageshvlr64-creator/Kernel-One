"""Shared domain entity types (docs/domain/) for all services.

Imported by services/ — never the reverse (docs/15_CODEBASE_TARGET_STRUCTURE.md).
Field names match docs/schemas/06_model_schema.md exactly.
"""

from .models import (
    Capability,
    DataClassification,
    Model,
    Provider,
    _CLASSIFICATION_ORDER,
)

__all__ = [
    "Capability",
    "DataClassification",
    "Model",
    "Provider",
    "_CLASSIFICATION_ORDER",
]
