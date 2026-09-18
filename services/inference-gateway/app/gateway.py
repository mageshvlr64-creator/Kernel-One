"""Core inference pipeline for the Inference Gateway.

Flow per docs/features/03_inference_gateway/:
  1. Validate the request (explicit model_id OR selection criteria).
  2. Resolve the model: explicit ID is passed through; selection criteria
     are sent to the model-router's POST /api/v1/models/select.
  3. Execute via the provider adapter with the runtime timeout budget.
  4. On retryable failure (MODEL_UNAVAILABLE / INFERENCE_TIMEOUT): retry
     once, then walk the router's fallback chain.
  5. Report every attempt's outcome to the router (circuit breaker feed).
  6. Persist an audit event for every inference call.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Awaitable, Callable, Optional

from .adapter_base import BaseAdapter, ProviderError
from .adapters import ADAPTERS
from .config import GatewayConfig
from .router_client import RouterClient, RouterUnavailableError
from .schemas import InferenceRequest, InferenceResponse

logger = logging.getLogger(__name__)

# Error codes that justify a retry / fallback walk (runtime/11_retry_policy.md)
_RETRYABLE_CODES = {"MODEL_UNAVAILABLE", "INFERENCE_TIMEOUT"}


class GatewayValidationError(Exception):
    """Request failed gateway-level validation (surface as HTTP 422)."""


class InferenceGateway:
    """Provider-agnostic inference execution with fallback and audit."""

    def __init__(
        self,
        config: GatewayConfig,
        router_client: RouterClient,
        audit_repo=None,
        sleep: Optional[Callable[[float], Awaitable[None]]] = None,
        wait_for: Optional[Callable[..., Awaitable[Any]]] = None,
    ) -> None:
        self._config = config
        self._router = router_client
        self._audit_repo = audit_repo
        # Injectable sleep for retry backoff (default asyncio.sleep): tests
        # record backoff scheduling without real delays, the same seam the
        # model-router's poll loop uses.
        self._sleep: Callable[[float], Awaitable[None]] = (
            sleep if sleep is not None else asyncio.sleep
        )
        # Injectable wait_for for the per-request timeout budget (default
        # asyncio.wait_for): tests capture which budget each request kind
        # receives and simulate expiry instantly.
        self._wait_for: Callable[..., Awaitable[Any]] = (
            wait_for if wait_for is not None else asyncio.wait_for
        )

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def infer(
        self, request: InferenceRequest, x_roles: str
    ) -> InferenceResponse:
        """Run one inference request end-to-end."""
        start = time.monotonic()

        # 1. Validate: exactly one of model_id / selection (empty dict counts
        # as a provided selection — an explicit "pick for me" with no criteria)
        if (request.model_id is None) == (request.selection is None):
            raise GatewayValidationError(
                "Exactly one of 'model_id' or 'selection' must be provided"
            )

        # 2. Resolve candidates: [explicit] or [selected] + fallback chain
        candidates: list[str]
        if request.model_id:
            candidates = [request.model_id]
        else:
            try:
                ref, fallback = await self._router.select(request.selection, x_roles)
            except RouterUnavailableError as exc:
                await self._audit(
                    actor_id=x_roles, model_id=None, provider=None,
                    result="error", error_code="MODEL_UNAVAILABLE",
                    details=f"router: {exc}", latency_ms=0.0,
                )
                raise ProviderError(
                    "MODEL_UNAVAILABLE", "No model available",
                    details=exc.details,
                ) from exc
            candidates = [ref.id] + [m for m in fallback if m != ref.id]

        # 3. Execute with retry + fallback walk
        last_error: Optional[ProviderError] = None
        for index, model_id in enumerate(candidates):
            for attempt in range(self._config.max_retries + 1):
                try:
                    response = await self._execute_one(model_id, request)
                    response.fallback_used = index > 0
                    await self._router.report_result(model_id, True, None, x_roles)
                    await self._audit(
                        actor_id=x_roles, model_id=model_id,
                        provider=response.provider, result="success",
                        latency_ms=(time.monotonic() - start) * 1000,
                    )
                    return response
                except ProviderError as exc:
                    last_error = exc
                    await self._router.report_result(
                        model_id, False, exc.error_code, x_roles
                    )
                    retriable = exc.error_code in _RETRYABLE_CODES
                    has_retry_left = attempt < self._config.max_retries
                    logger.warning(
                        "Inference failed model=%s attempt=%d code=%s retriable=%s",
                        model_id, attempt + 1, exc.error_code, retriable,
                    )
                    if retriable and has_retry_left:
                        await self._sleep(self._config.retry_backoff_seconds)
                        continue
                    break  # move to next candidate

        # 4. Everything failed
        code = last_error.error_code if last_error else "INTERNAL_ERROR"
        message = str(last_error) if last_error else "no candidates attempted"
        await self._audit(
            actor_id=x_roles, model_id=candidates[0] if candidates else None,
            provider=None, result="error", error_code=code,
            details=message, latency_ms=(time.monotonic() - start) * 1000,
        )
        raise last_error if last_error else ProviderError("INTERNAL_ERROR", message)

    # ------------------------------------------------------------------
    # Single-model execution
    # ------------------------------------------------------------------

    async def _execute_one(
        self, model_id: str, request: InferenceRequest
    ) -> InferenceResponse:
        adapter = self._adapter_for(model_id)
        # Runtime timeout budget per kind (30s text / 60s vision) — the
        # adapter's own client timeout is the second safety net.
        budget = (
            self._config.inference_timeout_vision_seconds
            if request.kind.value == "vision"
            else self._config.inference_timeout_text_seconds
        )
        try:
            return await self._wait_for(
                adapter.generate(model_id, request), timeout=budget
            )
        except asyncio.TimeoutError as exc:
            raise ProviderError(
                "INFERENCE_TIMEOUT",
                f"Inference exceeded {budget:.0f}s budget on {model_id}",
            ) from exc

    def _adapter_for(self, model_id: str) -> BaseAdapter:
        """Resolve the adapter for a model ID.

        Provider routing uses the model-router as source of truth: the
        gateway asks the router which provider serves this model by
        selecting with an explicit ID filter when needed. For simplicity,
        adapters are keyed by provider prefix in the model ID
        (e.g. 'vllm/qwen2.5-coder-7b'), falling back to the selection
        path when the ID carries no prefix.
        """
        provider = None
        if "/" in model_id:
            provider = model_id.split("/", 1)[0]
        if provider and provider in ADAPTERS:
            return ADAPTERS[provider]
        # Unknown prefix — default to vllm per DEC-004 (primary runtime);
        # a wrong guess fails fast with MODEL_UNAVAILABLE and the fallback
        # chain handles the rest.
        return ADAPTERS["vllm"]

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------

    async def _audit(
        self,
        *,
        actor_id: Optional[str],
        model_id: Optional[str],
        provider: Optional[str],
        result: str,
        error_code: Optional[str] = None,
        details: Optional[str] = None,
        latency_ms: Optional[float] = None,
    ) -> None:
        if self._audit_repo is None:
            return
        try:
            await self._audit_repo.record(
                actor_id=actor_id, model_id=model_id, provider=provider,
                result=result, error_code=error_code, details=details,
                latency_ms=latency_ms,
            )
        except Exception as exc:  # audit must never break inference
            logger.error("Failed to persist inference audit event: %s", exc)
