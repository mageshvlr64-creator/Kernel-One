"""Model registry — the authoritative store of registered models.

The registry is the source of truth for:
- Which models exist and their metadata
- Real-time availability (kept in sync via health polling)
- Per-model provider base URLs

On startup, models are loaded from the registry config file (MODEL_REGISTRY_PATH)
and then kept in memory; health status is updated by the background poller.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Awaitable, Callable, Optional

import httpx

from .config import ModelRouterConfig
from .models import (
    Capability,
    DataClassification,
    Model,
    ModelHealth,
    Provider,
)

logger = logging.getLogger(__name__)


class RegistryConfigError(RuntimeError):
    """MODEL_REGISTRY_PATH contents are malformed — fail fast at boot.

    Deliberately not a registry-API error code: this is a configuration
    failure raised before the service can serve traffic, not a request
    failure with a wire representation.
    """


class ModelRegistry:
    """In-memory model registry with background health polling.

    Lifecycle:
    1. ``load()`` — parse MODEL_REGISTRY_PATH JSON into models
    2. ``start_health_polling()`` — background task updates ``is_available``
    3. ``stop_health_polling()`` — cancel background task
    """

    def __init__(
        self,
        config: ModelRouterConfig,
        sleep: Optional[Callable[[float], Awaitable[None]]] = None,
    ) -> None:
        self._config = config
        self._models: dict[str, Model] = {}
        self._health: dict[str, ModelHealth] = {}
        self._poll_task: Optional[asyncio.Task[None]] = None
        self._http_client: Optional[httpx.AsyncClient] = None
        # Injectable sleep for the poll loop: production uses asyncio.sleep;
        # tests supply a fake so loop timing (interval honored, one health
        # check per round) is verified without real delays.
        self._sleep: Callable[[float], Awaitable[None]] = (
            sleep if sleep is not None else asyncio.sleep
        )

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    async def load(self) -> None:
        """Load models from MODEL_REGISTRY_PATH.

        Expected JSON format:
        {
          "models": [
            { ... Model fields ... },
            ...
          ]
        }

        Tolerated modes (documented start-empty behavior):
        - MODEL_REGISTRY_PATH unset -> start empty
        - file absent               -> start empty

        Everything else is strict and atomic: invalid JSON, a non-object
        root, a missing or non-list "models" key, any malformed entry, or
        a duplicate model id raise RegistryConfigError so the service
        fails fast at boot instead of silently running with a partial
        catalog. The registry is only mutated after every entry has
        validated, so a failed load never leaves a half-loaded state.
        """
        path = self._config.model_registry_path
        if not path:
            logger.warning(
                "MODEL_REGISTRY_PATH not set — starting with empty registry"
            )
            return

        p = Path(path)
        if not p.exists():
            logger.warning("Registry file %s not found — starting empty", path)
            return

        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise RegistryConfigError(
                f"registry file {p} is not valid JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise RegistryConfigError(
                f"registry file {p} must contain a JSON object")
        raw_models = data.get("models")
        if not isinstance(raw_models, list):
            raise RegistryConfigError(
                f"registry file {p} must have a \"models\" array")

        loaded: dict[str, Model] = {}
        seen: dict[str, int] = {}
        for index, raw in enumerate(raw_models):
            label = raw.get("id") if isinstance(raw, dict) else raw
            try:
                model = Model(**raw)
            except Exception as exc:
                raise RegistryConfigError(
                    f"registry file {p}, models[{index}] ({label!r}): {exc}"
                ) from exc
            if model.id in seen:
                raise RegistryConfigError(
                    f"registry file {p}, models[{index}]: duplicate model id "
                    f"{model.id!r} (first seen at models[{seen[model.id]}])")
            seen[model.id] = index
            loaded[model.id] = model

        self._models.update(loaded)
        logger.info("Loaded %d models from registry", len(loaded))

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get(self, model_id: str) -> Optional[Model]:
        """Return a model by ID, or None."""
        return self._models.get(model_id)

    def list_all(self) -> list[Model]:
        """Return all registered models."""
        return list(self._models.values())

    def list_available(self) -> list[Model]:
        """Return only models marked available and whose circuit breaker is closed."""
        return [m for m in self._models.values() if m.is_available]

    def filter_by_capabilities(
        self, required: list[Capability]
    ) -> list[Model]:
        """Return available models that have ALL required capabilities."""
        if not required:
            return self.list_available()
        return [
            m
            for m in self.list_available()
            if all(c in m.capabilities for c in required)
        ]

    def filter_by_classification(
        self, max_classification: DataClassification
    ) -> list[Model]:
        """Return available models whose max_classification >= the given level.

        A model with max_classification=CONFIDENTIAL can serve PUBLIC, INTERNAL,
        and CONFIDENTIAL requests.
        """
        from .models import _CLASSIFICATION_ORDER

        ceiling = _CLASSIFICATION_ORDER[max_classification]
        return [
            m
            for m in self.list_available()
            if _CLASSIFICATION_ORDER[m.max_classification] >= ceiling
        ]

    # ------------------------------------------------------------------
    # Mutations (admin API)
    # ------------------------------------------------------------------

    def set_available(self, model_id: str, available: bool) -> bool:
        """Set a model's availability. Returns False if model not found."""
        model = self._models.get(model_id)
        if model is None:
            return False
        # Create a new model instance with updated availability
        updated = model.model_copy(update={"is_available": available})
        self._models[model_id] = updated
        return True

    def register_model(self, model: Model) -> None:
        """Register or update a model in the registry."""
        self._models[model.id] = model

    def unregister_model(self, model_id: str) -> bool:
        """Remove a model from the registry. Returns False if not found."""
        if model_id not in self._models:
            return False
        del self._models[model_id]
        self._health.pop(model_id, None)
        return True

    # ------------------------------------------------------------------
    # Health polling
    # ------------------------------------------------------------------

    async def start_health_polling(self) -> None:
        """Start background health polling for all registered models."""
        self._http_client = httpx.AsyncClient(
            timeout=self._config.health_check_timeout_seconds
        )
        self._poll_task = asyncio.create_task(self._poll_loop())
        logger.info("Health polling started (interval=%.1fs)", self._config.health_poll_interval_seconds)

    async def stop_health_polling(self) -> None:
        """Stop the background health poller and close the HTTP client."""
        if self._poll_task is not None:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    async def _poll_loop(self) -> None:
        """Periodically check health of every registered model."""
        while True:
            await self._sleep(self._config.health_poll_interval_seconds)
            await self._check_all_health()

    async def _check_all_health(self) -> None:
        """Check health of all models concurrently."""
        if self._http_client is None:
            return
        tasks = [self._check_health(model) for model in self._models.values()]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_health(self, model: Model) -> None:
        """Check a single model's health via its provider endpoint."""
        base_url = self._provider_base_url(model.provider)
        health_url = self._health_endpoint(model.provider, base_url)

        start = time.monotonic()
        try:
            resp = await self._http_client.get(health_url)  # type: ignore[union-attr]
            latency_ms = (time.monotonic() - start) * 1000
            healthy = resp.status_code == 200
            error = None if healthy else f"HTTP {resp.status_code}"
        except Exception as exc:
            latency_ms = (time.monotonic() - start) * 1000
            healthy = False
            error = str(exc)

        health = ModelHealth(
            model_id=model.id,
            provider=model.provider,
            is_healthy=healthy,
            latency_ms=round(latency_ms, 2),
            last_check=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            error=error,
        )
        self._health[model.id] = health

        # Update model availability based on health
        if model.is_available != healthy:
            self.set_available(model.id, healthy)
            logger.info(
                "Model %s availability changed to %s (error=%s)",
                model.id,
                healthy,
                error,
            )

    def get_health(self, model_id: str) -> Optional[ModelHealth]:
        """Return the last health check result for a model."""
        return self._health.get(model_id)

    def get_all_health(self) -> list[ModelHealth]:
        """Return health status for all models."""
        return list(self._health.values())

    # ------------------------------------------------------------------
    # Provider URL helpers
    # ------------------------------------------------------------------

    def _provider_base_url(self, provider: Provider) -> str:
        return {
            Provider.VLLM: self._config.vllm_base_url,
            Provider.OLLAMA: self._config.ollama_base_url,
            Provider.LLAMACPP: self._config.llamacpp_base_url,
        }[provider]

    def _health_endpoint(self, provider: Provider, base_url: str) -> str:
        """Return the health-check URL for a given provider.

        Per integrations docs:
        - vLLM: GET /health
        - Ollama: GET /api/tags
        - llama.cpp: GET /health (OpenAI-compatible)
        """
        if provider == Provider.OLLAMA:
            return f"{base_url}/api/tags"
        return f"{base_url}/health"
