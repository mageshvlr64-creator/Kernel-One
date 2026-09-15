"""Unit tests for the InferenceGateway core pipeline.

The RouterClient is replaced with a fake; adapters are stubbed so no
real HTTP happens. Focus: candidate ordering, retry, fallback walk,
result reporting, audit emission.
"""

import pytest

from app.gateway import InferenceGateway
from app.adapter_base import BaseAdapter, ProviderError
from app.config import GatewayConfig
from app.schemas import InferenceKind, InferenceRequest, InferenceResponse


class FakeRouterClient:
    """Returns a canned selection or raises."""

    def __init__(self, ref=None, fallback=None, error=None):
        self.ref = ref
        self.fallback = fallback or []
        self.error = error
        self.reported = []  # list of (model_id, success, error_code)

    async def select(self, selection, x_roles):
        if self.error:
            raise self.error
        return self.ref, self.fallback

    async def report_result(self, model_id, success, error_code, x_roles):
        self.reported.append((model_id, success, error_code))


class StubAdapter(BaseAdapter):
    """Returns a fixed response or raises per model_id."""

    def __init__(self, outcomes: dict[str, object]):
        # Skip BaseAdapter's __init__ — no HTTP client needed
        self._outcomes = outcomes  # model_id -> InferenceResponse | Exception

    async def generate(self, model_id, request):
        outcome = self._outcomes[model_id]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    async def health_check(self):
        return True, None


def _make_ref(model_id="primary-model", provider="vllm"):
    from app.schemas import ModelRef

    return ModelRef(
        id=model_id,
        provider=provider,
        context_window=32768,
        max_classification="CONFIDENTIAL",
    )


def _make_request(**overrides) -> InferenceRequest:
    defaults = dict(
        messages=[{"role": "user", "content": "hello"}],
        selection={"required_capabilities": ["coding"]},
    )
    defaults.update(overrides)
    return InferenceRequest(**defaults)


def _make_gateway(adapter, router) -> InferenceGateway:
    config = GatewayConfig(max_retries=1, retry_backoff_seconds=0.0)
    gw = InferenceGateway(config, router, audit_repo=None)
    gw._adapter_for = lambda model_id: adapter  # type: ignore[method-assign]
    return gw


AUDIT_EVENTS = []


class RecordingRepo:
    async def record(self, **kwargs):
        AUDIT_EVENTS.append(kwargs)


@pytest.fixture(autouse=True)
def _clean_audit():
    AUDIT_EVENTS.clear()
    yield
    AUDIT_EVENTS.clear()


class TestValidation:
    async def test_both_model_id_and_selection_rejected(self):
        gw = _make_gateway(StubAdapter({}), FakeRouterClient())
        with pytest.raises(Exception, match="Exactly one"):
            await gw.infer(
                _make_request(model_id="m", selection={"a": 1}), "Operator"
            )

    async def test_neither_model_id_nor_selection_rejected(self):
        gw = _make_gateway(StubAdapter({}), FakeRouterClient())
        with pytest.raises(Exception, match="Exactly one"):
            await gw.infer(_make_request(selection=None), "Operator")


class TestExplicitModel:
    async def test_explicit_model_skips_router_select(self):
        resp = InferenceResponse(
            content="hi", model_id="m1", provider="vllm", latency_ms=1.0
        )
        router = FakeRouterClient()
        gw = _make_gateway(StubAdapter({"m1": resp}), router)

        result = await gw.infer(_make_request(selection=None, model_id="m1"), "Operator")

        assert result.model_id == "m1"
        assert result.fallback_used is False
        assert router.reported == [("m1", True, None)]


class TestSelection:
    async def test_selection_uses_router(self):
        resp = InferenceResponse(
            content="hi", model_id="primary", provider="vllm", latency_ms=1.0
        )
        router = FakeRouterClient(ref=_make_ref("primary"))
        gw = _make_gateway(StubAdapter({"primary": resp}), router)

        result = await gw.infer(_make_request(), "Operator")

        assert result.model_id == "primary"
        assert result.fallback_used is False
        assert router.reported == [("primary", True, None)]

    async def test_router_unavailable_maps_to_model_unavailable(self):
        from app.router_client import RouterUnavailableError

        router = FakeRouterClient(error=RouterUnavailableError("router down"))
        gw = _make_gateway(StubAdapter({}), router)

        with pytest.raises(ProviderError) as excinfo:
            await gw.infer(_make_request(), "Operator")

        assert excinfo.value.error_code == "MODEL_UNAVAILABLE"


class TestRetryAndFallback:
    async def test_retry_once_then_succeed(self):
        calls = {"n": 0}

        class FlakyAdapter(StubAdapter):
            async def generate(self, model_id, request):
                calls["n"] += 1
                if calls["n"] == 1:
                    raise ProviderError("MODEL_UNAVAILABLE", "down")
                return InferenceResponse(
                    content="ok", model_id=model_id, provider="vllm", latency_ms=1.0
                )

        router = FakeRouterClient()
        gw = _make_gateway(FlakyAdapter({}), router)

        result = await gw.infer(
            _make_request(selection=None, model_id="m1"), "Operator"
        )
        assert result.model_id == "m1"
        assert calls["n"] == 2  # 1 retry allowed

    async def test_fallback_chain_walked_on_failure(self):
        primary_resp = InferenceResponse(
            content="ok", model_id="secondary", provider="vllm", latency_ms=1.0
        )
        failing = ProviderError("MODEL_UNAVAILABLE", "down")
        adapter = StubAdapter(
            {"primary": failing, "secondary": primary_resp}
        )
        router = FakeRouterClient(
            ref=_make_ref("primary"), fallback=["secondary"]
        )
        gw = _make_gateway(adapter, router)

        result = await gw.infer(_make_request(), "Operator")

        assert result.model_id == "secondary"
        assert result.fallback_used is True
        # primary reports both attempts (initial + retry), then secondary succeeds
        assert router.reported == [
            ("primary", False, "MODEL_UNAVAILABLE"),
            ("primary", False, "MODEL_UNAVAILABLE"),
            ("secondary", True, None),
        ]

    async def test_all_candidates_fail_raises_last_error(self):
        failing = ProviderError("MODEL_UNAVAILABLE", "down")
        adapter = StubAdapter({"primary": failing, "secondary": failing})
        router = FakeRouterClient(ref=_make_ref("primary"), fallback=["secondary"])
        gw = _make_gateway(adapter, router)

        with pytest.raises(ProviderError) as excinfo:
            await gw.infer(_make_request(), "Operator")

        assert excinfo.value.error_code == "MODEL_UNAVAILABLE"
        # primary: 2 attempts (initial + retry), secondary: 2 attempts
        assert len(router.reported) == 4

    async def test_non_retryable_error_not_retried(self):
        calls = {"n": 0}

        class ExhaustedAdapter(StubAdapter):
            async def generate(self, model_id, request):
                calls["n"] += 1
                raise ProviderError("MODEL_RESOURCE_EXHAUSTED", "OOM")

        router = FakeRouterClient(ref=_make_ref("primary"), fallback=["secondary"])
        adapter = ExhaustedAdapter({})
        gw = _make_gateway(adapter, router)

        with pytest.raises(ProviderError) as excinfo:
            await gw.infer(_make_request(), "Operator")

        assert excinfo.value.error_code == "MODEL_RESOURCE_EXHAUSTED"
        # No retry within the same model — straight to the fallback candidate
        assert calls["n"] == 2  # primary once + secondary once


class TestVisionTimeoutBudget:
    async def test_vision_uses_longer_budget(self, monkeypatch):
        from app.gateway import _RETRYABLE_CODES  # noqa: F401  (import sanity)

        class BudgetProbeAdapter(StubAdapter):
            async def generate(self, model_id, request):
                # Indirectly confirm kind-driven budget by checking config
                return InferenceResponse(
                    content="ok", model_id=model_id, provider="vllm", latency_ms=1.0
                )

        config = GatewayConfig(
            inference_timeout_text_seconds=5.0,
            inference_timeout_vision_seconds=9.0,
            max_retries=0,
        )
        gw = InferenceGateway(config, FakeRouterClient(), audit_repo=None)
        captured = {}

        async def fake_wait_for(coro, timeout):
            captured["timeout"] = timeout
            return await coro

        monkeypatch.setattr("app.gateway.asyncio.wait_for", fake_wait_for)

        adapter = BudgetProbeAdapter({})
        gw._adapter_for = lambda model_id: adapter  # type: ignore[method-assign]

        await gw.infer(
            _make_request(
                selection=None, model_id="m1", kind=InferenceKind.VISION
            ),
            "Operator",
        )
        assert captured["timeout"] == 9.0


class TestAudit:
    async def test_success_emits_audit_event(self):
        resp = InferenceResponse(
            content="hi", model_id="m1", provider="vllm", latency_ms=1.0
        )
        gw = _make_gateway(StubAdapter({"m1": resp}), FakeRouterClient())
        gw._audit_repo = RecordingRepo()

        await gw.infer(_make_request(selection=None, model_id="m1"), "Engineer")

        assert len(AUDIT_EVENTS) == 1
        event = AUDIT_EVENTS[0]
        assert event["result"] == "success"
        assert event["model_id"] == "m1"
        assert event["provider"] == "vllm"

    async def test_failure_emits_audit_event(self):
        adapter = StubAdapter({"m1": ProviderError("INFERENCE_TIMEOUT", "slow")})
        gw = _make_gateway(adapter, FakeRouterClient())
        gw._audit_repo = RecordingRepo()

        with pytest.raises(ProviderError):
            await gw.infer(
                _make_request(selection=None, model_id="m1"), "Engineer"
            )

        assert len(AUDIT_EVENTS) == 1
        event = AUDIT_EVENTS[0]
        assert event["result"] == "error"
        assert event["error_code"] == "INFERENCE_TIMEOUT"
