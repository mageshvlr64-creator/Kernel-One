"""Wire schemas for the Inference Gateway.

Provider-agnostic inference contract: callers (agent kernel, tools, UI)
send an InferenceRequest; the gateway routes it through the model-router
to the right provider adapter, and returns a normalized InferenceResponse.

Field names align with the Model schema (docs/schemas/06_model_schema.md)
and the audit event shape used by the model-router service.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class InferenceKind(str, Enum):
    """Which kind of generation is requested — drives timeout budgets."""

    TEXT = "text"
    VISION = "vision"


class Message(BaseModel):
    """A single chat message (OpenAI-style, shared by all providers)."""

    role: str = Field(pattern="^(system|user|assistant|tool)$")
    content: str


class ModelRef(BaseModel):
    """A model reference as returned by the model-router's /select endpoint."""

    id: str
    provider: str  # "vllm" | "ollama" | "llamacpp"
    context_window: int = Field(ge=1)
    max_classification: str


class InferenceRequest(BaseModel):
    """Provider-agnostic inference request.

    Either ``model_id`` (explicit) or ``selection`` (router picks) must be
    provided — enforced in the gateway service layer, not here.
    """

    messages: list[Message] = Field(min_length=1)
    kind: InferenceKind = InferenceKind.TEXT

    # Explicit model — skips the router's /select call
    model_id: Optional[str] = None

    # Or selection criteria — the gateway asks the model-router to pick
    selection: Optional[dict[str, Any]] = None

    # Generation parameters (passed through to the provider)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    temperature: Optional[float] = Field(default=None, ge=0, le=2)
    top_p: Optional[float] = Field(default=None, ge=0, le=1)
    stop: Optional[list[str]] = None


class InferenceResponse(BaseModel):
    """Normalized response — identical shape regardless of provider."""

    content: str
    model_id: str
    provider: str
    finish_reason: Optional[str] = None
    usage: Optional[dict[str, int]] = None
    latency_ms: float
    fallback_used: bool = False


class GatewayError(BaseModel):
    """Error envelope — error_code comes from docs/reference/01_error_codes.md."""

    error_code: str  # MODEL_UNAVAILABLE | MODEL_RESOURCE_EXHAUSTED | INFERENCE_TIMEOUT | INTERNAL_ERROR
    message: str
    details: Optional[str] = None
    model_id: Optional[str] = None
