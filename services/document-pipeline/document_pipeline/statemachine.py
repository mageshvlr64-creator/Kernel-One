"""Document state machine — docs/runtime/_state_machines_canonical.md (canonical, read-only).

The runtime's transition-guard validates against the JSON form pinned in the canonical file;
this module is that guard for the Document machine. Illegal transitions raise
RegistryError(RESOURCE_CONFLICT) — never a silent allowance. Only Document-Ingestion-owned
transitions are triggerable from this service; INDEXING -> READY is owned by Knowledge
Fabric and is deliberately not offered here (this increment's pipeline ends at INDEXING).
"""
from __future__ import annotations

from typing import Dict, FrozenSet

from .errors import RegistryError

# docs/runtime/_state_machines_canonical.md#document (human-readable table, JSON-equivalent)
STATES = ("UPLOADED", "VALIDATING", "EXTRACTING", "OCR", "INDEXING", "READY", "FAILED", "DELETED")

# (from, to) -> owning component. Owners outside document-pipeline are listed for the
# transition map's completeness but raise RegistryError when triggered from this service.
TRANSITIONS: Dict[tuple, str] = {
    ("UPLOADED", "VALIDATING"): "document_ingestion",
    ("VALIDATING", "EXTRACTING"): "document_ingestion",
    ("VALIDATING", "FAILED"): "document_ingestion",
    ("EXTRACTING", "OCR"): "document_ingestion",
    ("EXTRACTING", "INDEXING"): "document_ingestion",
    ("EXTRACTING", "FAILED"): "document_ingestion",
    ("OCR", "INDEXING"): "ocr",                    # feature group 11, later increment
    ("OCR", "FAILED"): "ocr",
    ("INDEXING", "READY"): "knowledge_fabric",     # feature group 13, Character 3 later increment
    ("INDEXING", "FAILED"): "knowledge_fabric",
    ("READY", "DELETED"): "document_ingestion",
}

OWNER_ALIASES = {"document_ingestion", "ocr"}  # owners inside document-pipeline's scope


def can_transition(current: str, new: str) -> bool:
    return (current, new) in TRANSITIONS


def transition(current: str, new: str, *, owner: str = "document_ingestion") -> str:
    """Apply a transition; illegal ones raise RESOURCE_CONFLICT (canonical error behavior)."""
    expected_owner = TRANSITIONS.get((current, new))
    if expected_owner is None:
        raise RegistryError(
            "RESOURCE_CONFLICT",
            operator_detail=f"illegal Document transition {current} -> {new}",
        )
    if owner not in OWNER_ALIASES or owner != expected_owner:
        raise RegistryError(
            "RESOURCE_CONFLICT",
            operator_detail=(
                f"transition {current} -> {new} is owned by {expected_owner!r}, "
                f"not {owner!r}"
            ),
        )
    return new
