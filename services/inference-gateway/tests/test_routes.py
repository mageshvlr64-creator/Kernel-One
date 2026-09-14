"""Route-level tests for the inference-gateway FastAPI app.

Uses FastAPI TestClient — no real router, DB, or providers. The shared
gateway's RouterClient is monkeypatched with a fake; adapters are
stubbed per test.
"""

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.adapter_base import BaseAdapter, ProviderError
from app.gateway import InferenceGateway
from app.schemas import InferenceResponse


class FakeRouterClient:
    def __init__(self, ref=None, fallback=None, error=None):
        self.ref = ref
        self.fallback = fallback or []
        self.error = error
        self.reported = []

    async def select(self, selection, x_roles):
        if self.error:
            raise self.error
        return self.ref, self.fallback

    async def report_result(self, model_id, success, error_code, x_roles):
        self.reported.append((model_id, success, error_code))

    async def close(self):
        pass


class StubAdapter(BaseAdapter):
    def __init__(self, outcomes):
        self._outcomes = outcomes

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
        id=model_id, provider=provider, context_window=32768,
        max_classification="CONFIDENTIAL",
    )


@pytest.fixture(autouse=True)
def _reset_shared_state():
    """Snapshot and restore the module-level gateway/adapters per test."""
    from app.adapters import ADAPTERS

    saved_gateway = main_module._gateway
    saved_router = main_module._router_client
    saved_adapters = dict(ADAPTERS)
    yield
    main_module._gateway = saved_gateway
    main_module._router_client = saved_router
    ADAPTERS.clear()
    ADAPTERS.update(saved_adapters)


@pytest.fixture
def client():
    return TestClient(main_module.app, headers={"x-roles": "Operator"})


def _install(fake_router, adapter):
    """Wire fake router + stubbed adapters into the shared gateway."""
    config = main_module._config
    main_module._gateway = InferenceGateway(config, fake_router, None)
    main_module._router_client = fake_router
    from app.adapters import ADAPTERS

    ADAPTERS.clear()
    for provider in ("vllm", "ollama", "llamacpp"):
        ADAPTERS[provider] = adapter


def _ok_response(model_id, provider="vllm"):
    return InferenceResponse(
        content="hello!", model_id=model_id, provider=provider, latency_ms=12.5
    )


class TestInfer:
    def test_infer_with_selection(self, client):
        router = FakeRouterClient(ref=_make_ref("primary-model"))
        adapter = StubAdapter({"primary-model": _ok_response("primary-model")})
        _install(router, adapter)

        resp = client.post(
            "/api/v1/infer",
            json={
                "messages": [{"role": "user", "content": "hi"}],
                "selection": {"required_capabilities": ["coding"]},
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["content"] == "hello!"
        assert body["model_id"] == "primary-model"
        assert body["provider"] == "vllm"
        assert body["fallback_used"] is False

    def test_infer_with_explicit_model_id(self, client):
        router = FakeRouterClient()
        adapter = StubAdapter({"m1": _ok_response("m1", provider="ollama")})
        _install(router, adapter)

        resp = client.post(
            "/api/v1/infer",
            json={
                "messages": [{"role": "user", "content": "hi"}],
                "model_id": "m1",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["model_id"] == "m1"
        assert resp.json()["provider"] == "ollama"

    def test_infer_fallback_used_flag(self, client):
        router = FakeRouterClient(ref=_make_ref("primary"), fallback=["secondary"])
        adapter = StubAdapter(
            {
                "primary": ProviderError("MODEL_UNAVAILABLE", "down"),
                "secondary": _ok_response("secondary"),
            }
        )
        _install(router, adapter)

        resp = client.post(
            "/api/v1/infer",
            json={
                "messages": [{"role": "user", "content": "hi"}],
                "selection": {},
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["model_id"] == "secondary"
        assert body["fallback_used"] is True

    def test_infer_all_fail_503_envelope(self, client):
        router = FakeRouterClient(ref=_make_ref("primary"))
        adapter = StubAdapter(
            {"primary": ProviderError("INFERENCE_TIMEOUT", "too slow")}
        )
        _install(router, adapter)

        resp = client.post(
            "/api/v1/infer",
            json={
                "messages": [{"role": "user", "content": "hi"}],
                "selection": {},
            },
        )
        assert resp.status_code == 503
        detail = resp.json()["detail"]
        assert detail["error_code"] == "INFERENCE_TIMEOUT"

    def test_infer_router_down_503(self, client):
        from app.router_client import RouterUnavailableError

        router = FakeRouterClient(error=RouterUnavailableError("router down"))
        adapter = StubAdapter({})
        _install(router, adapter)

        resp = client.post(
            "/api/v1/infer",
            json={
                "messages": [{"role": "user", "content": "hi"}],
                "selection": {},
            },
        )
        assert resp.status_code == 503
        assert resp.json()["detail"]["error_code"] == "MODEL_UNAVAILABLE"

    def test_infer_validation_error_422(self, client):
        router = FakeRouterClient()
        adapter = StubAdapter({})
        _install(router, adapter)

        resp = client.post(
            "/api/v1/infer",
            json={
                "messages": [{"role": "user", "content": "hi"}],
                "model_id": "m1",
                "selection": {"a": 1},
            },
        )
        assert resp.status_code == 422

    def test_infer_missing_both_422(self, client):
        router = FakeRouterClient()
        adapter = StubAdapter({})
        _install(router, adapter)

        resp = client.post(
            "/api/v1/infer",
            json={"messages": [{"role": "user", "content": "hi"}]},
        )
        assert resp.status_code == 422

    def test_infer_bad_message_role_422(self, client):
        router = FakeRouterClient()
        adapter = StubAdapter({})
        _install(router, adapter)

        resp = client.post(
            "/api/v1/infer",
            json={
                "messages": [{"role": "wizard", "content": "hi"}],
                "model_id": "m1",
            },
        )
        assert resp.status_code == 422


class TestPermissions:
    def test_no_roles_denied(self):
        router = FakeRouterClient()
        adapter = StubAdapter({})
        _install(router, adapter)
        anon = TestClient(main_module.app)  # no x-roles header

        resp = anon.post(
            "/api/v1/infer",
            json={"messages": [{"role": "user", "content": "hi"}], "model_id": "m1"},
        )
        assert resp.status_code == 403

    def test_auditor_cannot_infer(self):
        router = FakeRouterClient()
        adapter = StubAdapter({})
        _install(router, adapter)
        auditor = TestClient(main_module.app, headers={"x-roles": "Auditor"})

        resp = auditor.post(
            "/api/v1/infer",
            json={"messages": [{"role": "user", "content": "hi"}], "model_id": "m1"},
        )
        assert resp.status_code == 403

    def test_operator_can_view_provider_health(self, client):
        router = FakeRouterClient()
        adapter = StubAdapter({})
        _install(router, adapter)

        resp = client.get("/api/v1/providers/health")
        assert resp.status_code == 200
        providers = {p["provider"] for p in resp.json()}
        assert providers == {"vllm", "ollama", "llamacpp"}
        assert all(p["is_healthy"] for p in resp.json())


class TestProbes:
    def test_healthz(self, client):
        resp = client.get("/healthz")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_readyz(self, client):
        router = FakeRouterClient()
        adapter = StubAdapter({})
        _install(router, adapter)

        resp = client.get("/readyz")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] in ("ok", "degraded")
        assert body["checks"]["adapters"] == "ok"
