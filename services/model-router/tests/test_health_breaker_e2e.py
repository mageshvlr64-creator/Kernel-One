"""End-to-end tests for health polling and circuit-breaker-driven routing.

Exercises the REAL app singletons (``_registry``, ``_circuit_breaker``)
through the FastAPI TestClient, so each test covers the full chain the
service runs in production:

    HTTP route -> registry / router -> circuit breaker -> selection

Provider endpoints are faked with ``httpx.MockTransport`` injected into the
registry's HTTP client — the same seam the background health poller uses —
so the polling tests run the registry's real ``_check_health`` /
``_check_all_health`` code paths without any network.

Isolation note: ``unregister_model`` does not clear a model's circuit
breaker state, so the autouse fixture resets breakers explicitly (this
pins current behavior; it is not an endorsement of it).
"""

from __future__ import annotations

import time

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import _circuit_breaker, _registry, app
from app.models import CircuitState


@pytest.fixture(autouse=True)
def _reset_state():
    """Empty the registry and breakers around each test; no stray HTTP client."""
    for m in _registry.list_all():
        _registry.unregister_model(m.id)
    for model_id in list(_circuit_breaker._breakers):
        _circuit_breaker.reset(model_id)
    yield
    for m in _registry.list_all():
        _registry.unregister_model(m.id)
    for model_id in list(_circuit_breaker._breakers):
        _circuit_breaker.reset(model_id)
    _registry._http_client = None


@pytest.fixture
def client():
    """TestClient acting as an Administrator (full role set)."""
    return TestClient(app, headers={"x-roles": "Administrator"})


def _register(client, model_id, params=4.0, provider="vllm"):
    """Register a coding model via the real admin route."""
    resp = client.post(
        "/api/v1/models",
        json={
            "id": model_id,
            "display_name": f"Test {model_id}",
            "provider": provider,
            "total_parameters_billions": params,
            "context_window": 32768,
            "capabilities": ["coding"],
            "max_classification": "CONFIDENTIAL",
            "is_available": True,
        },
    )
    assert resp.is_success, resp.text


def _select(client):
    return client.post(
        "/api/v1/models/select", json={"required_capabilities": ["coding"]}
    )


def _report(client, model_id, success):
    resp = client.post(
        "/api/v1/models/report-result",
        json={"model_id": model_id, "success": success},
    )
    assert resp.status_code == 204


def _trip(client, model_id, failures=5):
    """Drive the breaker OPEN through the real report-result route."""
    for _ in range(failures):
        _report(client, model_id, success=False)


async def _run_provider_health_check(status_by_port):
    """Run the registry's real health check against faked provider ports.

    Ports mirror the config defaults: vllm :8000, ollama :11434,
    llama.cpp :8080. Any port not in *status_by_port* answers 200.
    """
    def handler(request: httpx.Request) -> httpx.Response:
        port = request.url.port or 80
        return httpx.Response(status_by_port.get(port, 200))

    original = _registry._http_client
    _registry._http_client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), timeout=2.0
    )
    try:
        await _registry._check_all_health()
    finally:
        await _registry._http_client.aclose()
        _registry._http_client = original


class TestHealthPollingDrivesAvailability:
    async def test_unhealthy_poll_marks_unavailable_and_blocks_selection(self, client):
        _register(client, "alpha")
        await _run_provider_health_check({8000: 500})

        health = _registry.get_health("alpha")
        assert health is not None
        assert health.is_healthy is False
        assert _registry.get("alpha").is_available is False
        assert _select(client).status_code == 503

    async def test_healthy_poll_keeps_model_selectable(self, client):
        _register(client, "alpha")
        await _run_provider_health_check({8000: 200})

        assert _registry.get_health("alpha").is_healthy is True
        assert _registry.get("alpha").is_available is True
        resp = _select(client)
        assert resp.status_code == 200
        assert resp.json()["model"]["id"] == "alpha"

    async def test_recovery_poll_restores_availability(self, client):
        _register(client, "alpha")
        await _run_provider_health_check({8000: 500})
        assert _registry.get("alpha").is_available is False

        await _run_provider_health_check({8000: 200})
        assert _registry.get("alpha").is_available is True
        assert _select(client).status_code == 200

    async def test_check_all_health_without_client_is_a_noop(self, client):
        _register(client, "alpha")
        await _registry._check_all_health()  # no HTTP client injected
        assert _registry.get_health("alpha") is None


class TestBreakerDrivenFallback:
    async def test_failures_trip_breaker_and_route_to_fallback(self, client):
        _register(client, "primary", params=4.0)
        _register(client, "backup", params=8.0)
        assert _select(client).json()["model"]["id"] == "primary"

        _trip(client, "primary")
        assert _circuit_breaker.get_state("primary") == CircuitState.OPEN
        assert _select(client).json()["model"]["id"] == "backup"

    async def test_tripped_only_model_returns_503(self, client):
        _register(client, "only")
        _trip(client, "only")
        assert _select(client).status_code == 503

    async def test_success_report_resets_failure_count(self, client):
        _register(client, "only")
        _trip(client, "only", failures=4)
        _report(client, "only", success=True)

        _trip(client, "only", failures=4)
        assert _circuit_breaker.get_state("only") == CircuitState.CLOSED
        assert _select(client).status_code == 200

        _report(client, "only", success=False)
        assert _circuit_breaker.get_state("only") == CircuitState.OPEN

    async def test_window_expiry_forgives_old_failures(self, client):
        _register(client, "only")
        _trip(client, "only", failures=2)
        breaker = _circuit_breaker._breakers["only"]
        breaker.last_failure_time = time.monotonic() - 61.0  # outside the 60s window

        _trip(client, "only", failures=3)
        assert _circuit_breaker.get_state("only") == CircuitState.CLOSED

        _trip(client, "only", failures=2)
        assert _circuit_breaker.get_state("only") == CircuitState.OPEN

    async def test_half_open_probe_success_closes_circuit(self, client):
        _register(client, "primary", params=4.0)
        _register(client, "backup", params=8.0)
        _trip(client, "primary")
        # Rewind opened_at past the 15s half-open probe window.
        _circuit_breaker._breakers["primary"].opened_at -= 16.0

        assert _select(client).json()["model"]["id"] == "primary"  # probe allowed
        _report(client, "primary", success=True)
        assert _circuit_breaker.get_state("primary") == CircuitState.CLOSED
        assert _select(client).json()["model"]["id"] == "primary"

    async def test_half_open_probe_failure_reopens_immediately(self, client):
        _register(client, "primary", params=4.0)
        _register(client, "backup", params=8.0)
        _trip(client, "primary")
        _circuit_breaker._breakers["primary"].opened_at -= 16.0

        assert _select(client).json()["model"]["id"] == "primary"  # one probe allowed
        _report(client, "primary", success=False)
        assert _circuit_breaker.get_state("primary") == CircuitState.OPEN
        assert _select(client).json()["model"]["id"] == "backup"

    async def test_breakers_are_independent_per_model(self, client):
        _register(client, "primary", params=4.0)
        _register(client, "backup", params=8.0)
        _trip(client, "primary")

        assert _circuit_breaker.get_state("backup") == CircuitState.CLOSED
        assert _select(client).json()["model"]["id"] == "backup"


class TestPollerLifecycle:
    async def test_start_stop_polling_round_trip(self, client):
        _register(client, "alpha")
        await _registry.start_health_polling()
        try:
            assert _registry._poll_task is not None
            assert not _registry._poll_task.done()
        finally:
            await _registry.stop_health_polling()
        assert _registry._poll_task is None
        assert _registry._http_client is None
