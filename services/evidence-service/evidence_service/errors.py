"""Canonical error registry bindings for evidence-service.

Source of truth: docs/reference/01_error_codes.md (owned by Characters 1/5).
Rule: this feature returns errors exclusively from that registry — no local codes.
Wire shape per docs/api/26_error_contracts.md and docs/schemas/02_api_schema.md.

Rows mirror knowledge-fabric's bindings; the Evidence feature docs (§17) name
FILE_NOT_FOUND, RAG_INDEX_UNAVAILABLE, and INTERNAL_ERROR as the codes most
relevant to this feature. INVALID_REQUEST / AUTH_REQUIRED / TOOL_NOT_ALLOWED /
POLICY_DENIED / FILE_CLASSIFICATION_DENIED are shared plumbing (schema, auth,
policy gates) used by every service in the platform.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class RegistryEntry:
    code: str
    http_status: int
    user_message: str
    audit_required: bool


# Rows evidence-and-provenance ops may return (subset of reference/01_error_codes.md).
# Values (HTTP status, user message) are copied verbatim from the canonical registry.
REGISTRY: Dict[str, RegistryEntry] = {
    "INVALID_REQUEST": RegistryEntry("INVALID_REQUEST", 400, "Your request couldn't be processed — check the highlighted fields.", True),
    "AUTH_REQUIRED": RegistryEntry("AUTH_REQUIRED", 401, "Please sign in to continue.", True),
    "POLICY_DENIED": RegistryEntry("POLICY_DENIED", 403, "You don't have permission to do this.", True),
    "TOOL_NOT_ALLOWED": RegistryEntry("TOOL_NOT_ALLOWED", 403, "This action isn't available for your role.", True),
    "FILE_CLASSIFICATION_DENIED": RegistryEntry("FILE_CLASSIFICATION_DENIED", 403, "You don't have access to this document.", True),
    "FILE_NOT_FOUND": RegistryEntry("FILE_NOT_FOUND", 404, "That item couldn't be found.", False),
    "RESOURCE_CONFLICT": RegistryEntry("RESOURCE_CONFLICT", 409, "This item was already updated by someone else.", True),
    "RAG_INDEX_UNAVAILABLE": RegistryEntry("RAG_INDEX_UNAVAILABLE", 503, "Search is temporarily unavailable.", True),
    "DEPENDENCY_UNAVAILABLE": RegistryEntry("DEPENDENCY_UNAVAILABLE", 503, "A required service is temporarily unavailable.", True),
    "INTERNAL_ERROR": RegistryEntry("INTERNAL_ERROR", 500, "Something went wrong on our end.", True),
}


class RegistryError(Exception):
    """An error whose code is one of docs/reference/01_error_codes.md."""

    def __init__(self, code: str, details: Optional[List[Dict[str, str]]] = None,
                 operator_detail: str = "",
                 resource_id: Optional[str] = None) -> None:
        entry = REGISTRY.get(code)
        if entry is None:
            # Fail loud: an unregistered code must never leak into a response.
            raise ValueError(f"error code {code!r} is not in docs/reference/01_error_codes.md")
        self.code = code
        self.http_status = entry.http_status
        self.user_message = entry.user_message
        self.audit_required = entry.audit_required
        self.details = details  # field-level errors; populated only for INVALID_REQUEST
        self.operator_detail = operator_detail
        # Optional: the resource the error refers to, for the matching audit event.
        self.resource_id = resource_id
        super().__init__(f"{code}: {operator_detail or entry.user_message}")

    def error_envelope(self, correlation_id: str) -> Dict[str, Any]:
        """ApiErrorEnvelope per docs/schemas/02_api_schema.md."""
        return {
            "error": {
                "code": self.code,
                "message": self.user_message,
                "details": {"field_errors": self.details} if self.details else None,
                "correlation_id": correlation_id,
            }
        }
