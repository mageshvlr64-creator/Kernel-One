"""Tests for the gateway's timing behavior via injectable seams.

``InferenceGateway`` takes ``sleep`` (retry backoff) and ``wait_for``
(timeout budgets) callables, defaulting to ``asyncio.sleep`` /
``asyncio.wait_for``. With recording fakes, timing behavior is verified
without a single real delay:

- which backoff interval is scheduled on each retryable failure
- which timeout budget each request kind receives (text vs vision)
- timeout expiry surfaces as INFERENCE_TIMEOUT instantly
- adapters map HTTP timeout exceptions to canonical error codes via
  ``httpx.MockTransport`` (no network, no clock dependence)
"""

from __future__ import annotations

import asyncio
import httpx
import pytest

from app.adapter_base import BaseAdapter, ProviderError
from app.adapters import ADAPTERS
from app.adapters.llamacpp import LlamaCppAdapter
from app.adapters.ollama import OllamaAdapter
from app.adapters.vllm import VllmAdapter
from app.config import GatewayConfig
from app.gateway import InferenceGateway
from app.schemas import InferenceKind, InferenceRequest, InferenceResponse


class RecordingSleep:
    """Records backoff scheduling; no real delay."""

    def __init__(self) -> None:
        self.calls: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)


class RecordingWaitFor:
    """Delegates to asyncio.wait_for but records each timeout budget."""

    def __init__(self) -> None:
        self.budgets: list[float] = []

    async def __call__(self, aw, timeout=None):
        self.budgets.append(timeout)
        return await asyncio.wait_for(aw, timeout=timeout)


class ExpiringWaitFor:
    """Simulates budget expiry instantly — no real delay."""

    async def __call__(self, aw, timeout=None):
        aw.close()  # avoid un-awaited coroutine warnings
        raise asyncio.TimeoutError()


def _resp(content: str = "hi") -> InferenceResponse:
    return InferenceResponse(content=content, model_id="m", provider="vllm", latency_ms=1.0)


class FakeRouter:
    def __init__(self, ref=None, fallback=None):
        self.ref = ref
        self.fallback = fallback or []
        self.reported = []

    async def select(self, selection, x_roles):
        return self.ref, self.fallback

    async def report_result(self, model_id, success, error_code, x_roles):
        self.reported.append((model_id, success, error_code))


class FixedAdapter(BaseAdapter):
    """Succeeds or raises per call, in order."""

    def __init__(self, outcomes):
        self._outcomes = list(outcomes)

    async def generate(self, model_id, request):
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    async def health_check(self):
        return True, None


def _make_gateway(adapter, router=None, sleep=None, wait_for=None):
    config = GatewayConfig(max_retries=1, retry_backoff_seconds=2.5)
    gw = InferenceGateway(config, router or FakeRouter(), audit_repo=None, sleep=sleep, wait_for=wait_for)
    gw._adapter_for = lambda model_id: adapter  # type: ignore[method-assign]
    return gw


def _make_request(**overrides) -> InferenceRequest:
    defaults = dict(
        messages=[{"role": "user", "content": "hello"}],
        selection={"required_capabilities": ["coding"]},
    )
    defaults.update(overrides)
    return InferenceRequest(**defaults)


class TestRetryBackoffScheduling:
    async def test_backoff_interval_recorded_not_slept(self):
        sleep = RecordingSleep()
        adapter = FixedAdapter([
            ProviderError("MODEL_UNAVAILABLE", "down"),
            _resp(),
        ])
        router = FakeRouter()
        gw = _make_gateway(adapter, router, sleep=sleep)
        result = await gw.infer(_make_request(selection=None, model_id="m"), "Operator")
        assert result.model_id == "m"
        assert sleep.calls == [2.5]  # one retry, configured interval, no real sleep
        assert router.reported == [("m", False, "MODEL_UNAVAILABLE"), ("m", True, None)]

    async def test_no_backoff_for_non_retryable_failure(self):
        sleep = RecordingSleep()
        adapter = FixedAdapter([
            ProviderError("MODEL_RESOURCE_EXHAUSTED", "oom"),
            _resp(),
        ])
        router = FakeRouter()
        gw = _make_gateway(adapter, router, sleep=sleep)
        # Non-retryable codes skip backoff AND the same-model retry: the
        # gateway fails over immediately — with no other candidate, it raises.
        with pytest.raises(ProviderError) as exc_info:
            await gw.infer(_make_request(selection=None, model_id="m"), "Operator")
        assert exc_info.value.error_code == "MODEL_RESOURCE_EXHAUSTED"
        assert sleep.calls == []  # no backoff was ever scheduled
        assert router.reported == [("m", False, "MODEL_RESOURCE_EXHAUSTED")]


class TestTimeoutBudgets:
    async def test_text_request_gets_text_budget(self):
        wf = RecordingWaitFor()
        gw = _make_gateway(FixedAdapter([_resp()]), wait_for=wf)
        await gw.infer(_make_request(selection=None, model_id="m", kind=InferenceKind.TEXT), "Operator")
        config = GatewayConfig()
        assert wf.budgets == [config.inference_timeout_text_seconds]

    async def test_vision_request_gets_vision_budget(self):
        wf = RecordingWaitFor()
        gw = _make_gateway(FixedAdapter([_resp()]), wait_for=wf)
        await gw.infer(_make_request(selection=None, model_id="m", kind=InferenceKind.VISION), "Operator")
        config = GatewayConfig()
        assert wf.budgets == [config.inference_timeout_vision_seconds]

    async def test_timeout_expiry_maps_to_inference_timeout(self):
        gw = _make_gateway(FixedAdapter([_resp()]), wait_for=ExpiringWaitFor())
        with pytest.raises(ProviderError) as exc_info:
            await gw.infer(_make_request(selection=None, model_id="m"), "Operator")
        assert exc_info.value.error_code == "INFERENCE_TIMEOUT"


class TestAdapterTimeoutMapping:
    """Real adapters, faked transport: HTTP timeout → canonical error code."""

    @staticmethod
    def _timeout_transport() -> httpx.MockTransport:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectTimeout("provider silent", request=request)

        return httpx.MockTransport(handler)

    @pytest.mark.parametrize("adapter_cls", [VllmAdapter, OllamaAdapter, LlamaCppAdapter])
    async def test_generate_timeout_maps_to_inference_timeout(self, adapter_cls):
        adapter = adapter_cls(base_url="http://provider.test", timeout_seconds=1.0)
        adapter._client = httpx.AsyncClient(
            base_url="http://provider.test",
            timeout=1.0,
            transport=self._timeout_transport(),
        )
        request = _make_request(selection=None, model_id="x/m")
        with pytest.raises(ProviderError) as exc_info:
            await adapter.generate("x/m", request)
        assert exc_info.value.error_code == "INFERENCE_TIMEOUT"
        await adapter.close()

    @pytest.mark.parametrize("adapter_cls", [VllmAdapter, OllamaAdapter, LlamaCppAdapter])
    async def test_health_check_timeout_reports_unhealthy(self, adapter_cls):
        adapter = adapter_cls(base_url="http://provider.test", timeout_seconds=1.0)
        adapter._client = httpx.AsyncClient(
            base_url="http://provider.test",
            timeout=1.0,
            transport=self._timeout_transport(),
        )
        healthy, detail = await adapter.health_check()
        assert healthy is False
        assert detail  # error detail is present
        await adapter.close()
