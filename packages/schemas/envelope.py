"""API envelopes from docs/schemas/02_api_schema.md — canonical shapes."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ApiSuccessEnvelope(BaseModel):
    """Every 2xx response: {"data": <payload>, "pagination"?: {...}}."""

    data: Any
    pagination: Optional[dict[str, Any]] = None


class ApiErrorEnvelope(BaseModel):
    """Every non-2xx response per docs/api/26_error_contracts.md."""

    error: ErrorBody


class ErrorBody(BaseModel):
    code: str  # one of docs/reference/01_error_codes.md
    message: str  # exact user message from the registry
    details: Optional[dict[str, Any]] = None  # only for INVALID_REQUEST
    correlation_id: Optional[str] = None  # uuid; ties to AuditEvent
