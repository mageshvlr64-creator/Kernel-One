"""Model selection router.

Core routing logic:
1. Filter models by capabilities, classification, provider, size, context window
2. Apply circuit-breaker gating
3. Rank remaining candidates (prefer requested provider, then smallest sufficient model)
4. Return selection with fallback chain for the caller

Fallback routing per features/02_model_router/09_fallback_routing.md:
when the primary model is unavailable (circuit breaker open), the router
walks the ranked fallback chain until one is available or all are exhausted.
"""

from __future__ import annotations

import logging
from typing import Optional

from .circuit_breaker import CircuitBreaker
from .models import (
    AuditEvent,
    Capability,
    DataClassification,
    Model,
    ModelSelectionRequest,
    ModelSelectionResponse,
    Provider,
    _CLASSIFICATION_ORDER,
)
from .registry import ModelRegistry

logger = logging.getLogger(__name__)


class ModelRouter:
    """Selects the best model for a given request, with fallback.

    The router is stateless — all state lives in the ModelRegistry and
    CircuitBreaker instances it receives at construction time.
    """

    def __init__(
        self,
        registry: ModelRegistry,
        circuit_breaker: CircuitBreaker,
    ) -> None:
        self._registry = registry
        self._circuit_breaker = circuit_breaker

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------

    def select(
        self,
        request: ModelSelectionRequest,
        actor_id: Optional[str] = None,
    ) -> tuple[Optional[ModelSelectionResponse], AuditEvent]:
        """Select the best model for *request*.

        Returns:
            (response, audit_event) — response is None when no model matches.

        The audit_event is always populated; callers must emit it regardless
        of success/failure per developer rule 4 (every action is auditable).
        """
        candidates = self._build_candidate_list(request)

        if not candidates:
            event = AuditEvent(
                actor_id=actor_id,
                result="error",
                error_code="MODEL_UNAVAILABLE",
                details="No model matches the requested filters",
            )
            logger.warning("Model selection failed: no candidates for request")
            return None, event

        # Build fallback chain (ranked)
        ranked = self._rank(candidates, request.preferred_provider)

        # Walk the chain
        for model in ranked:
            if not self._circuit_breaker.allow_request(model.id):
                logger.debug(
                    "Circuit breaker OPEN for %s — skipping", model.id
                )
                continue

            fallback_ids = [m.id for m in ranked if m.id != model.id]
            response = ModelSelectionResponse(
                model=model,
                fallback_chain=fallback_ids,
                reason="best_match",
            )
            event = AuditEvent(
                actor_id=actor_id,
                model_id=model.id,
                provider=model.provider,
                classification=model.max_classification,
                result="success",
            )
            return response, event

        # All candidates had open circuit breakers
        event = AuditEvent(
            actor_id=actor_id,
            result="error",
            error_code="MODEL_UNAVAILABLE",
            details="All candidate models have open circuit breakers",
        )
        logger.warning(
            "Model selection failed: all %d candidates circuit-broken", len(ranked)
        )
        return None, event

    # ------------------------------------------------------------------
    # Candidate filtering
    # ------------------------------------------------------------------

    def _build_candidate_list(
        self, request: ModelSelectionRequest
    ) -> list[Model]:
        """Apply all filter criteria and return matching models."""
        models = self._registry.list_available()

        # 1. Required capabilities
        if request.required_capabilities:
            models = [
                m
                for m in models
                if all(c in m.capabilities for c in request.required_capabilities)
            ]

        # 2. Classification ceiling
        if request.max_classification is not None:
            ceiling = _CLASSIFICATION_ORDER[request.max_classification]
            models = [
                m
                for m in models
                if _CLASSIFICATION_ORDER[m.max_classification] >= ceiling
            ]

        # 3. Preferred provider (soft filter — prefer, don't require)
        # Handled in ranking, not filtering.

        # 4. Max parameters
        if request.max_parameters_billions is not None:
            models = [
                m
                for m in models
                if m.total_parameters_billions <= request.max_parameters_billions  # type: ignore[operator]
            ]

        # 5. Minimum context window
        if request.min_context_window is not None:
            models = [
                m
                for m in models
                if m.context_window >= request.min_context_window  # type: ignore[operator]
            ]

        return models

    # ------------------------------------------------------------------
    # Ranking
    # ------------------------------------------------------------------

    def _rank(
        self,
        candidates: list[Model],
        preferred_provider: Optional[Provider] = None,
    ) -> list[Model]:
        """Rank candidates: preferred provider first, then smallest sufficient.

        Ranking criteria (in priority order):
        1. Preferred provider (if specified)
        2. Fewer total parameters (smallest sufficient model)
        3. Lower max_classification (least-privilege: use the least-sensitive model)

        This implements a conservative strategy: use the smallest model that
        can do the job, preferring the provider the caller requested.
        """
        def sort_key(model: Model) -> tuple[int, float, int]:
            provider_penalty = 0
            if preferred_provider is not None and model.provider != preferred_provider:
                provider_penalty = 1
            return (
                provider_penalty,
                model.total_parameters_billions,
                _CLASSIFICATION_ORDER[model.max_classification],
            )

        return sorted(candidates, key=sort_key)

    # ------------------------------------------------------------------
    # Post-selection callbacks
    # ------------------------------------------------------------------

    def report_success(self, model_id: str) -> None:
        """Report a successful inference — resets circuit breaker."""
        self._circuit_breaker.record_success(model_id)

    def report_failure(self, model_id: str) -> None:
        """Report a failed inference — may trip circuit breaker."""
        self._circuit_breaker.record_failure(model_id)
