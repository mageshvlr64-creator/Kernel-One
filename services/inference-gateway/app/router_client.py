"""HTTP client for the model-router service.

The gateway never picks providers itself — it asks the model-router
(POST /api/v1/models/select) which model + fallback chain to use, and
reports the outcome back (POST /api/v1/models/report-result) so the
router can trip its circuit breakers (runtime/11_retry_policy.md).
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from .schemas import ModelRef

logger = logging.getLogger(__name__)


class RouterUnavailableError(Exception):
    """The model-router itself is unreachable or returned an error.

    Per docs/failures/10_model_unavailable.md, the gateway must surface
    MODEL_UNAVAILABLE — it cannot invent a model.
    """

    def __init__(self, message: str, details: Optional[str] = None) -> None:
        super().__init__(message)
        self.details = details


class RouterClient:
    """Async client for the model-router's public API."""

    def __init__(self, base_url: str, timeout_seconds: float = 5.0) -> None:
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

    async def select(
        self, selection: Optional[dict[str, Any]], x_roles: str
    ) -> tuple[ModelRef, list[str]]:
        """Ask the model-router to pick a model.

        Returns (selected model ref, fallback chain of model IDs).
        Raises RouterUnavailableError if the router is down or no model
        matches (HTTP 503 from the router means MODEL_UNAVAILABLE).
        """
        client = await self._get_client()
        payload: dict[str, Any] = dict(selection or {})
        try:
            resp = await client.post(
                f"{self._base_url}/api/v1/models/select",
                json=payload,
                headers={"x-roles": x_roles},
            )
        except httpx.TimeoutException as exc:
            raise RouterUnavailableError("Model router did not respond in time") from exc
        except httpx.HTTPError as exc:
            raise RouterUnavailableError(
                "Model router not reachable", details=str(exc)
            ) from exc

        if resp.status_code == 503:
            # Router had no matching model — surface as MODEL_UNAVAILABLE
            raise RouterUnavailableError(
                "No model available for request",
                details=str(resp.json().get("detail", resp.text)[:500]),
            )
        if resp.status_code == 403:
            raise RouterUnavailableError("POLICY_DENIED by model router")
        if resp.status_code != 200:
            raise RouterUnavailableError(
                f"Model router returned HTTP {resp.status_code}",
                details=resp.text[:500],
            )

        data = resp.json()
        model_data = data.get("model", {})
        try:
            ref = ModelRef(
                id=model_data["id"],
                provider=model_data["provider"],
                context_window=model_data["context_window"],
                max_classification=model_data["max_classification"],
            )
        except (KeyError, TypeError) as exc:
            raise RouterUnavailableError(
                "Model router returned malformed selection", details=str(data)[:500]
            ) from exc

        fallback_chain = list(data.get("fallback_chain") or [])
        return ref, fallback_chain

    async def report_result(
        self, model_id: str, success: bool, error_code: Optional[str], x_roles: str
    ) -> None:
        """Report inference outcome so the router updates its circuit breaker.

        Best-effort: failures are logged, never raised — an audit-reporting
        failure must not fail the caller's request.
        """
        client = await self._get_client()
        body = {"model_id": model_id, "success": success, "error_code": error_code}
        try:
            resp = await client.post(
                f"{self._base_url}/api/v1/models/report-result",
                json=body,
                headers={"x-roles": x_roles},
            )
            if resp.status_code not in (200, 204):
                logger.warning(
                    "report-result for %s returned HTTP %s", model_id, resp.status_code
                )
        except httpx.HTTPError as exc:
            logger.warning("report-result for %s failed: %s", model_id, exc)
