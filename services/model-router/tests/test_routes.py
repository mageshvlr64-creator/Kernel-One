"""Route-level tests for the model-router FastAPI app.

Uses FastAPI TestClient — no real DB, no real HTTP to providers.
All repo deps are overridden with in-memory equivalents.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app, _registry, _circuit_breaker, _model_router


@pytest.fixture(autouse=True)
def _reset_state():
    """Clear registry between tests."""
    # Remove all models from the in-memory registry
    for m in _registry.list_all():
        _registry.unregister_model(m.id)
    yield
    for m in _registry.list_all():
        _registry.unregister_model(m.id)


@pytest.fixture
def client():
    """TestClient with an Administrator role by default."""
    return TestClient(app, headers={"x-roles": "Administrator"})


@pytest.fixture
def read_client():
    """TestClient with an Operator (read-only) role."""
    return TestClient(app, headers={"x-roles": "Operator"})


@pytest.fixture
def no_role_client():
    """TestClient with no roles header."""
    return TestClient(app, headers={})


def _register_test_model(
    client,
    model_id="test-model",
    provider="vllm",
    capabilities=None,
    classification="CONFIDENTIAL",
):
    """Helper to register a model via the API."""
    return client.post("/api/v1/models", json={
        "id": model_id,
        "display_name": f"Test {model_id}",
        "provider": provider,
        "total_parameters_billions": 7.0,
        "context_window": 32768,
        "capabilities": capabilities or ["coding"],
        "max_classification": classification,
        "is_available": True,
    })


class TestListModels:
    def test_empty(self, client):
        resp = client.get("/api/v1/models")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_with_models(self, client):
        _register_test_model(client)
        resp = client.get("/api/v1/models")
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestGetModel:
    def test_found(self, client):
        _register_test_model(client, model_id="m1")
        resp = client.get("/api/v1/models/m1")
        assert resp.status_code == 200
        assert resp.json()["id"] == "m1"

    def test_not_found(self, client):
        resp = client.get("/api/v1/models/nonexistent")
        assert resp.status_code == 404


class TestCreateModel:
    def test_create(self, client):
        resp = _register_test_model(client, model_id="new-model")
        assert resp.status_code == 201
        assert resp.json()["id"] == "new-model"

    def test_update_existing(self, client):
        _register_test_model(client, model_id="m1")
        resp = _register_test_model(client, model_id="m1")
        assert resp.status_code == 201

    def test_read_only_cannot_create(self, read_client):
        resp = _register_test_model(read_client, model_id="m1")
        assert resp.status_code == 403


class TestDeleteModel:
    def test_delete(self, client):
        _register_test_model(client, model_id="m1")
        resp = client.delete("/api/v1/models/m1")
        assert resp.status_code == 204

        # Confirm gone
        resp = client.get("/api/v1/models/m1")
        assert resp.status_code == 404

    def test_delete_not_found(self, client):
        resp = client.delete("/api/v1/models/nonexistent")
        assert resp.status_code == 404


class TestSelectModel:
    def test_select(self, client):
        _register_test_model(client)
        resp = client.post("/api/v1/models/select", json={
            "required_capabilities": ["coding"],
        })
        assert resp.status_code == 200
        assert resp.json()["model"]["id"] == "test-model"

    def test_select_no_match(self, client):
        _register_test_model(client, capabilities=["vision"])
        resp = client.post("/api/v1/models/select", json={
            "required_capabilities": ["coding"],
        })
        assert resp.status_code == 503

    def test_select_empty_registry(self, client):
        resp = client.post("/api/v1/models/select", json={})
        assert resp.status_code == 503


class TestAvailability:
    def test_set_availability(self, client):
        _register_test_model(client, model_id="m1")
        resp = client.patch("/api/v1/models/m1/availability", json={
            "is_available": False,
        })
        assert resp.status_code == 200
        assert resp.json()["is_available"] is False

    def test_availability_not_found(self, client):
        resp = client.patch("/api/v1/models/nope/availability", json={
            "is_available": False,
        })
        assert resp.status_code == 404


class TestProbes:
    def test_healthz(self, client):
        resp = client.get("/healthz")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_readyz(self, client):
        resp = client.get("/readyz")
        assert resp.status_code == 200
        # No DB configured, but that's ok
        assert resp.json()["status"] in ("ok", "degraded")


class TestPermissionDenials:
    def test_no_roles_denied(self, no_role_client):
        resp = no_role_client.get("/api/v1/models")
        assert resp.status_code == 403

    def test_read_only_cannot_delete(self, read_client):
        _register_test_model(read_client, model_id="m1")
        resp = read_client.delete("/api/v1/models/m1")
        assert resp.status_code == 403
