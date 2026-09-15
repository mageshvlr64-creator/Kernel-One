"""llama.cpp adapter — CPU-fallback runtime (cpu-fallback capability, DEC-004).

Speaks llama-server's OpenAI-compatible API, normalized identically to
the vLLM/Ollama adapters per docs/integrations/04_llamacpp.md.
"""

from __future__ import annotations

import time
from typing import Any, Optional

import httpx

from ..adapter_base import BaseAdapter, ProviderError
from ..schemas import InferenceRequest, InferenceResponse


class LlamaCppAdapter(BaseAdapter):
    """Adapter for llama-server's OpenAI-compatible chat endpoint."""

    async def generate(
        self, model_id: str, request: InferenceRequest
    ) -> InferenceResponse:
        client = await self._get_client()
        payload = self._build_payload(model_id, request)
        url = f"{self._base_url}/v1/chat/completions"

        start = time.monotonic()
        try:
            resp = await client.post(url, json=payload)
        except Exception as exc:
            raise self._http_error_to_code(exc) from exc

        latency_ms = (time.monotonic() - start) * 1000

        if resp.status_code == 404:
            raise ProviderError(
                "MODEL_UNAVAILABLE",
                f"Model {model_id} not loaded in llama-server",
            )
        if resp.status_code >= 500:
            raise ProviderError(
                "MODEL_RESOURCE_EXHAUSTED",
                "llama-server capacity error",
                details=resp.text[:500],
            )
        if resp.status_code != 200:
            raise ProviderError(
                "MODEL_UNAVAILABLE",
                f"llama-server returned HTTP {resp.status_code}",
                details=resp.text[:500],
            )

        return self._parse_response(resp.json(), model_id, latency_ms)

    async def health_check(self) -> tuple[bool, Optional[str]]:
        client = await self._get_client()
        try:
            resp = await client.get(f"{self._base_url}/health")
            return resp.status_code == 200, None if resp.status_code == 200 else f"HTTP {resp.status_code}"
        except Exception as exc:
            return False, str(exc)

    # ------------------------------------------------------------------
    # Payload / response mapping
    # ------------------------------------------------------------------

    def _build_payload(self, model_id: str, request: InferenceRequest) -> dict[str, Any]:
        # llama-server ignores the model field but accepts it for compat
        payload: dict[str, Any] = {
            "model": model_id,
            "messages": [m.model_dump() for m in request.messages],
        }
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.top_p is not None:
            payload["top_p"] = request.top_p
        if request.stop is not None:
            payload["stop"] = request.stop
        return payload

    def _parse_response(
        self, data: dict[str, Any], model_id: str, latency_ms: float
    ) -> InferenceResponse:
        try:
            choice = data["choices"][0]
        except (KeyError, IndexError) as exc:
            raise ProviderError(
                "MODEL_UNAVAILABLE",
                "llama-server response missing choices",
                details=str(data)[:500],
            ) from exc

        return InferenceResponse(
            content=choice.get("message", {}).get("content", ""),
            model_id=model_id,
            provider="llamacpp",
            finish_reason=choice.get("finish_reason"),
            usage=data.get("usage"),
            latency_ms=round(latency_ms, 2),
        )
