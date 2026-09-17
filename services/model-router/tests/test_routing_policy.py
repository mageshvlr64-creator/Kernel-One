"""End-to-end routing policy — live app + populated registry + 4-model
catalog including a RESTRICTED-cleared model.

Classification policy (docs/reference/05_permission_matrix.md): a request
classified at level L may only be served by models whose max_classification
>= L. These tests pin that policy end-to-end through POST /api/v1/models/select
(app + router + registry + circuit breaker, no DB / no real providers).
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app, _registry
from app.models import (
    Capability,
    DataClassification,
    Model,
    Provider,
)


@pytest.fixture(autouse=True)
def catalog():
    """Populate the in-memory registry with the production 4-model catalog."""
    models = [
        Model(id="llama-3.1-8b-instruct", display_name="Llama 3.1 8B Instruct",
              provider=Provider.LLAMACPP, total_parameters_billions=8.0,
              quantization="Q4_K_M", context_window=128000,
              capabilities=[Capability.CODING, Capability.TOOL_CALLING,
                            Capability.STRUCTURED_OUTPUT],
              max_classification=DataClassification.CONFIDENTIAL),
        Model(id="qwen2.5-coder-7b-instruct", display_name="Qwen 2.5 Coder 7B",
              provider=Provider.VLLM, total_parameters_billions=7.6,
              quantization="FP16", context_window=32768,
              capabilities=[Capability.CODING, Capability.TOOL_CALLING,
                            Capability.STRUCTURED_OUTPUT],
              max_classification=DataClassification.CONFIDENTIAL),
        Model(id="deepseek-r1-distill-32b", display_name="DeepSeek R1 Distill 32B",
              provider=Provider.VLLM, total_parameters_billions=32.0,
              active_parameters_billions=3.5, quantization="AWQ-INT4",
              context_window=64000,
              capabilities=[Capability.CODING, Capability.TOOL_CALLING,
                            Capability.STRUCTURED_OUTPUT],
              max_classification=DataClassification.RESTRICTED),
        Model(id="llava-7b", display_name="LLaVA 7B (Vision)",
              provider=Provider.OLLAMA, total_parameters_billions=7.0,
              quantization="FP16", context_window=4096,
              capabilities=[Capability.VISION, Capability.OCR_ASSIST],
              max_classification=DataClassification.INTERNAL),
    ]
    for m in models:
        _registry.register_model(m)
    yield
    for m in _registry.list_all():
        _registry.unregister_model(m.id)


@pytest.fixture
def client():
    return TestClient(app, headers={"x-roles": "Operator"})


def _select(client, **filters):
    return client.post("/api/v1/models/select", json=filters)


class TestRoutingPolicyEndToEnd:
    def test_restricted_request_reaches_only_the_restricted_model(self, client):
        resp = _select(client, required_capabilities=["coding"],
                       max_classification="RESTRICTED")
        assert resp.status_code == 200
        chosen = resp.json()["model"]["id"]
        assert chosen == "deepseek-r1-distill-32b"

    def test_restricted_fallback_chain_never_leaks_downlevel_models(self, client):
        # fallback_chain lists ranked alternatives EXCLUDING the chosen model;
        # with deepseek the only RESTRICTED-eligible coder, the chain must be
        # empty — proving no down-level model is offered as a fallback.
        resp = _select(client, required_capabilities=["coding"],
                       max_classification="RESTRICTED")
        chain = resp.json()["fallback_chain"]
        assert chain == []

    def test_confidential_request_excludes_internal_only_llava(self, client):
        resp = _select(client, required_capabilities=["coding"],
                       max_classification="CONFIDENTIAL")
        assert resp.status_code == 200
        body = resp.json()
        ids = [body["model"]["id"]] + body["fallback_chain"]
        assert "llava-7b" not in ids
        assert set(ids) <= {"llama-3.1-8b-instruct", "qwen2.5-coder-7b-instruct",
                            "deepseek-r1-distill-32b"}

    def test_internal_request_may_use_all_three_text_models(self, client):
        resp = _select(client, required_capabilities=["coding"],
                       max_classification="INTERNAL")
        assert resp.status_code == 200
        ids = [resp.json()["model"]["id"]] + resp.json()["fallback_chain"]
        assert set(ids) == {"llama-3.1-8b-instruct", "qwen2.5-coder-7b-instruct",
                            "deepseek-r1-distill-32b"}

    def test_preferred_provider_honored_within_policy(self, client):
        resp = _select(client, required_capabilities=["coding"],
                       max_classification="RESTRICTED", preferred_provider="vllm")
        assert resp.status_code == 200
        assert resp.json()["model"]["id"] == "deepseek-r1-distill-32b"

    def test_vision_request_at_internal_still_routes_to_llava(self, client):
        resp = _select(client, required_capabilities=["vision"],
                       max_classification="INTERNAL")
        assert resp.status_code == 200
        assert resp.json()["model"]["id"] == "llava-7b"

    def test_context_window_filter_still_applies(self, client):
        resp = _select(client, required_capabilities=["coding"],
                       max_classification="INTERNAL", min_context_window=100000)
        assert resp.status_code == 200
        assert resp.json()["model"]["id"] == "llama-3.1-8b-instruct"

    def test_catalog_mirrors_models_json(self, catalog, client):
        """The test fixture and models.json must agree (drift alarm)."""
        import json
        from pathlib import Path
        catalog_file = json.loads(
            (Path(__file__).resolve().parents[1] / "models.json")
            .read_text(encoding="utf-8"))
        assert sorted(m["id"] for m in catalog_file["models"]) == \
            sorted(m.id for m in _registry.list_all())
