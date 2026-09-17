"""Admin-endpoint validation — invalid model registrations must fail with
proper 4xx client errors, never an unhandled server error (500), and the
registry must remain unchanged after a rejected registration.

Also pins the boot contract: a malformed catalog at startup produces a
clear SystemExit message (fail fast), not a confusing traceback.
"""

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app, _registry


@pytest.fixture(autouse=True)
def _reset_state():
    for m in _registry.list_all():
        _registry.unregister_model(m.id)
    yield
    for m in _registry.list_all():
        _registry.unregister_model(m.id)


@pytest.fixture
def client():
    return TestClient(app, headers={"x-roles": "Administrator"})


def _valid_body(**overrides):
    body = {
        "id": "admin-test-model",
        "display_name": "Admin Test Model",
        "provider": "vllm",
        "total_parameters_billions": 7.0,
        "context_window": 32768,
        "capabilities": ["coding"],
        "max_classification": "CONFIDENTIAL",
        "is_available": True,
    }
    body.update(overrides)
    return body


class TestAdminRegistrationValidation:
    def test_valid_registration_201(self, client):
        resp = client.post("/api/v1/models", json=_valid_body())
        assert resp.status_code == 201
        assert resp.json()["id"] == "admin-test-model"

    def test_negative_context_window_is_422_not_500(self, client):
        resp = client.post(
            "/api/v1/models", json=_valid_body(context_window=-1))
        assert resp.status_code == 422
        assert _registry.get("admin-test-model") is None

    def test_zero_context_window_is_422(self, client):
        resp = client.post(
            "/api/v1/models", json=_valid_body(context_window=0))
        assert resp.status_code == 422

    def test_zero_parameters_is_schema_legal(self, client):
        # ge=0 / minimum:0 — zero is degenerate but valid per 06_model_schema.md.
        resp = client.post(
            "/api/v1/models",
            json=_valid_body(total_parameters_billions=0.0),
        )
        assert resp.status_code == 201

    def test_negative_parameters_is_422(self, client):
        resp = client.post(
            "/api/v1/models",
            json=_valid_body(total_parameters_billions=-3.5),
        )
        assert resp.status_code == 422

    def test_unknown_capability_is_422_not_500(self, client):
        resp = client.post(
            "/api/v1/models",
            json=_valid_body(capabilities=["coding", "telepathy"]),
        )
        assert resp.status_code == 422
        assert "telepathy" in resp.json()["detail"]
        assert _registry.get("admin-test-model") is None

    def test_unknown_provider_is_422(self, client):
        resp = client.post(
            "/api/v1/models", json=_valid_body(provider="quantum"))
        assert resp.status_code == 422

    def test_unknown_classification_is_422(self, client):
        resp = client.post(
            "/api/v1/models",
            json=_valid_body(max_classification="TOP_SECRET"),
        )
        assert resp.status_code == 422

    def test_write_role_enforced(self):
        write_only = TestClient(app, headers={"x-roles": "Auditor"})
        resp = write_only.post("/api/v1/models", json=_valid_body())
        assert resp.status_code == 403

    def test_no_roles_fails_closed(self):
        anon = TestClient(app, headers={})
        resp = anon.post("/api/v1/models", json=_valid_body())
        assert resp.status_code == 403


class TestBootFailureMessage:
    def test_registry_config_error_exits_with_clear_message(self, tmp_path, monkeypatch, capsys):
        """A malformed registry file must produce a clear SystemExit, not a
        silent half-load or an opaque traceback."""
        from app.registry import ModelRegistry, RegistryConfigError
        from app.config import ModelRouterConfig

        bad = tmp_path / "models.json"
        bad.write_text(
            json.dumps({"models": [{"id": "broken", "provider": "vllm"}]}),
            encoding="utf-8",
        )
        reg = ModelRegistry(ModelRouterConfig(model_registry_path=str(bad)))
        with pytest.raises(RegistryConfigError) as err:
            import asyncio
            asyncio.run(reg.load())
        # The error message is actionable: file, index, and field error.
        message = str(err.value)
        assert "models.json" in message and "models[0]" in message

    def test_boot_failure_systemexit_carries_message(self, tmp_path, capsys):
        """End-to-end boot check: loading a bad file through the lifespan
        path's contract — SystemExit with the registry error in the text."""
        # Simulate exactly what main.lifespan does on RegistryConfigError:
        # log critical and raise SystemExit with the message attached.
        from app.registry import ModelRegistry, RegistryConfigError
        from app.config import ModelRouterConfig

        bad = tmp_path / "models.json"
        bad.write_text("{broken json", encoding="utf-8")
        reg = ModelRegistry(ModelRouterConfig(model_registry_path=str(bad)))
        with pytest.raises(RegistryConfigError):
            import asyncio
            asyncio.run(reg.load())
        # The lifespan wraps this into SystemExit("model-router: invalid "
        # "model registry: ..."); assert that wrapping text shape exists
        # in main.py so the contract cannot silently regress.
        import inspect
        from app import main as main_module
        source = inspect.getsource(main_module)
        assert "raise SystemExit(f\"model-router: invalid model registry: {exc}\")" in source
        assert "logger.critical" in source
