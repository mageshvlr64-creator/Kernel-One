"""Ollama adapter — secondary runtime (quick iteration / PROFILE-A fallback).

Speaks Ollama's native API (POST /api/chat), normalized to the internal
contract per docs/integrations/03_ollama.md.
"""

from __future__ import annotations

import time
from typing import Any, Optional

import httpx

from ..adapter_base import BaseAdapter, ProviderError
from ..schemas import InferenceRequest, InferenceResponse


class OllamaAdapter(BaseAdapter):
    """Adapter for Ollama's native /api/chat endpoint."""

    async def generate(
        self, model_id: str, request: InferenceRequest
    ) -> InferenceResponse:
        client = await self._get_client()
        payload = self._build_payload(model_id, request)
        url = f"{self._base_url}/api/chat"

        start = time.monotonic()
        try:
            resp = await client.post(url, json=payload)
        except Exception as exc:
            raise self._http_error_to_code(exc) from exc

        latency_ms = (time.monotonic() - start) * 1000

        if resp.status_code == 404:
            raise ProviderError(
                "MODEL_UNAVAILABLE",
                f"Model {model_id} not pulled on Ollama server",
            )
        if resp.status_code == 500 and "memory" in resp.text.lower():
            raise ProviderError(
                "MODEL_RESOURCE_EXHAUSTED",
                "Ollama out of memory",
                details=resp.text[:500],
            )
        if resp.status_code != 200:
            raise ProviderError(
                "MODEL_UNAVAILABLE",
                f"Ollama returned HTTP {resp.status_code}",
                details=resp.text[:500],
            )

        return self._parse_response(resp.json(), model_id, latency_ms)

    async def health_check(self) -> tuple[bool, Optional[str]]:
        """Ollama readiness probe is GET /api/tags per docs/integrations/03_ollama.md."""
        client = await self._get_client()
        try:
            resp = await client.get(f"{self._base_url}/api/tags")
            return resp.status_code == 200, None if resp.status_code == 200 else f"HTTP {resp.status_code}"
        except Exception as exc:
            return False, str(exc)

    # ------------------------------------------------------------------
    # Payload / response mapping
    # ------------------------------------------------------------------

    def _build_payload(self, model_id: str, request: InferenceRequest) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model_id,
            "messages": [m.model_dump() for m in request.messages],
            "stream": False,
        }
        options: dict[str, Any] = {}
        if request.max_tokens is not None:
            options["num_predict"] = request.max_tokens
        if request.temperature is not None:
            options["temperature"] = request.temperature
        if request.top_p is not None:
            options["top_p"] = request.top_p
        if request.stop is not None:
            options["stop"] = request.stop
        if options:
            payload["options"] = options
        return payload

    def _parse_response(
        self, data: dict[str, Any], model_id: str, latency_ms: float
    ) -> InferenceResponse:
        message = data.get("message", {})
        content = message.get("content", "")
        # Ollama signals truncation with done_reason "length"
        finish_reason = data.get("done_reason")
        eval_count = data.get("eval_count")
        prompt_count = data.get("prompt_eval_count")
        usage: Optional[dict[str, int]] = None
        if eval_count is not None or prompt_count is not None:
            usage = {
                "completion_tokens": eval_count or 0,
                "prompt_tokens": prompt_count or 0,
            }
        return InferenceResponse(
            content=content,
            model_id=model_id,
            provider="ollama",
            finish_reason=finish_reason,
            usage=usage,
            latency_ms=round(latency_ms, 2),
        )
