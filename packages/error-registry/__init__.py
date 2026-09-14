"""Canonical error registry — generated from docs/reference/01_error_codes.md.

Single source of truth for code → HTTP status → user message so no
endpoint invents its own copy (docs/api/26_error_contracts.md rule 2).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorSpec:
    code: str
    http_status: int
    user_message: str


_REGISTRY: dict[str, ErrorSpec] = {
    spec.code: spec
    for spec in [
        ErrorSpec("INVALID_REQUEST", 400, "Your request couldn't be processed — check the highlighted fields."),
        ErrorSpec("AUTH_REQUIRED", 401, "Please sign in to continue."),
        ErrorSpec("POLICY_DENIED", 403, "You don't have permission to do this."),
        ErrorSpec("TOOL_NOT_ALLOWED", 403, "This action isn't available for your role."),
        ErrorSpec("FILE_CLASSIFICATION_DENIED", 403, "You don't have access to this document."),
        ErrorSpec("APPROVAL_REQUIRED", 403, "This action needs approval before it can run."),
        ErrorSpec("APPROVAL_REJECTED", 403, "This action was not approved."),
        ErrorSpec("NETWORK_EGRESS_BLOCKED", 403, "This operation attempted a network connection that isn't allowed in this deployment."),
        ErrorSpec("MODEL_NOT_APPROVED", 403, "This request requires a model that isn't approved for this data's classification."),
        ErrorSpec("FILE_NOT_FOUND", 404, "That item couldn't be found."),
        ErrorSpec("RESOURCE_CONFLICT", 409, "This item was already updated by someone else."),
        ErrorSpec("MODEL_UNAVAILABLE", 503, "The AI model is temporarily unavailable — retrying."),
        ErrorSpec("MODEL_RESOURCE_EXHAUSTED", 503, "The system is at capacity — please try again shortly."),
        ErrorSpec("INFERENCE_TIMEOUT", 504, "The AI model took too long to respond."),
        ErrorSpec("RAG_INDEX_UNAVAILABLE", 503, "Search is temporarily unavailable."),
        ErrorSpec("DEPENDENCY_UNAVAILABLE", 503, "A required service is temporarily unavailable."),
        ErrorSpec("RATE_LIMITED", 429, "You're doing that too quickly — please wait a moment."),
        ErrorSpec("INTERNAL_ERROR", 500, "Something went wrong on our end."),
    ]
}


def get(code: str) -> ErrorSpec:
    """Return the canonical spec for a code, or INTERNAL_ERROR if unknown."""
    return _REGISTRY.get(code) or _REGISTRY["INTERNAL_ERROR"]


def http_status(code: str) -> int:
    return get(code).http_status


def user_message(code: str) -> str:
    return get(code).user_message


__all__ = ["ErrorSpec", "get", "http_status", "user_message"]
