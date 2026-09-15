"""Provider adapter base class.

Every adapter normalizes its provider's native API to the internal
InferenceResponse contract (schemas.py) — callers never know which
provider served a request except via the response's provider field
(per docs/integrations/03_ollama.md).
"""

from __future__ import annotations

import abc
from typing import Optional

import httpx

from .schemas import InferenceRequest, InferenceResponse


class ProviderError(Exception):
    """Raised by adapters on provider-level failures.

    ``error_code`` must come from docs/reference/01_error_codes.md:
    MODEL_UNAVAILABLE, MODEL_RESOURCE_EXHAUSTED, INFERENCE_TIMEOUT.
    """

    def __init__(self, error_code: str, message: str, details: Optional[str] = None) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.details = details


class BaseAdapter(abc.ABC):
    """Abstract provider adapter.

    Subclasses implement ``generate`` for their provider's native API.
    Timeouts are enforced by the gateway before calling the adapter, but
    adapters also apply their own client timeout as a second safety net.
    """

    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._timeout_seconds)
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    @abc.abstractmethod
    async def generate(
        self, model_id: str, request: InferenceRequest
    ) -> InferenceResponse:
        """Execute a chat-completion request against this provider."""

    @abc.abstractmethod
    async def health_check(self) -> tuple[bool, Optional[str]]:
        """Return (is_healthy, error_detail) for the provider's health endpoint."""

    def _http_error_to_code(self, exc: Exception) -> ProviderError:
        """Map an httpx exception to the canonical error registry."""
        if isinstance(exc, httpx.TimeoutException):
            return ProviderError("INFERENCE_TIMEOUT", "Provider did not respond in time")
        if isinstance(exc, httpx.ConnectError):
            return ProviderError(
                "MODEL_UNAVAILABLE", "Provider not reachable", details=str(exc)
            )
        return ProviderError(
            "MODEL_UNAVAILABLE", "Provider call failed", details=str(exc)
        )
