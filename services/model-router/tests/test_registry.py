"""Unit tests for the model registry (in-memory operations)."""

import pytest

from app.config import ModelRouterConfig
from app.models import Capability, DataClassification, Model, Provider
from app.registry import ModelRegistry


def _make_model(**overrides) -> Model:
    defaults = dict(
        id="test-model",
        display_name="Test Model",
        provider=Provider.VLLM,
        total_parameters_billions=7.0,
        context_window=32768,
        capabilities=[Capability.CODING],
        max_classification=DataClassification.CONFIDENTIAL,
        is_available=True,
    )
    defaults.update(overrides)
    return Model(**defaults)


@pytest.fixture
def registry():
    """Registry with no config file — starts empty."""
    config = ModelRouterConfig(model_registry_path="")
    return ModelRegistry(config)


@pytest.fixture
def populated_registry():
    """Registry pre-loaded with three models."""
    config = ModelRouterConfig(model_registry_path="")
    reg = ModelRegistry(config)

    reg.register_model(_make_model(
        id="vllm-7b", provider=Provider.VLLM,
        total_parameters_billions=7.0,
        capabilities=[Capability.CODING, Capability.TOOL_CALLING],
        max_classification=DataClassification.CONFIDENTIAL,
    ))
    reg.register_model(_make_model(
        id="ollama-vision", provider=Provider.OLLAMA,
        display_name="Vision Model",
        total_parameters_billions=7.0,
        context_window=4096,
        capabilities=[Capability.VISION, Capability.OCR_ASSIST],
        max_classification=DataClassification.INTERNAL,
    ))
    reg.register_model(_make_model(
        id="llamacpp-8b", provider=Provider.LLAMACPP,
        display_name="LLaMA 8B",
        total_parameters_billions=8.0,
        context_window=128000,
        capabilities=[Capability.CODING, Capability.TOOL_CALLING, Capability.STRUCTURED_OUTPUT],
        max_classification=DataClassification.PUBLIC,
    ))

    return reg


class TestRegistryBasic:
    def test_empty_registry(self, registry):
        assert registry.list_all() == []
        assert registry.get("nonexistent") is None

    def test_register_and_get(self, registry):
        model = _make_model(id="model-1")
        registry.register_model(model)
        assert registry.get("model-1") is not None
        assert registry.get("model-1").id == "model-1"

    def test_list_all(self, populated_registry):
        assert len(populated_registry.list_all()) == 3

    def test_unregister(self, populated_registry):
        assert populated_registry.unregister_model("vllm-7b") is True
        assert populated_registry.get("vllm-7b") is None
        assert len(populated_registry.list_all()) == 2

    def test_unregister_nonexistent(self, populated_registry):
        assert populated_registry.unregister_model("nope") is False


class TestRegistryAvailability:
    def test_set_available(self, populated_registry):
        populated_registry.set_available("vllm-7b", False)
        model = populated_registry.get("vllm-7b")
        assert model.is_available is False

    def test_list_available_excludes_unavailable(self, populated_registry):
        populated_registry.set_available("vllm-7b", False)
        available = populated_registry.list_available()
        ids = [m.id for m in available]
        assert "vllm-7b" not in ids
        assert len(available) == 2

    def test_set_available_nonexistent(self, populated_registry):
        assert populated_registry.set_available("nope", True) is False


class TestRegistryFiltering:
    def test_filter_by_capabilities(self, populated_registry):
        coding = populated_registry.filter_by_capabilities([Capability.CODING])
        ids = [m.id for m in coding]
        assert "ollama-vision" not in ids
        assert "vllm-7b" in ids
        assert "llamacpp-8b" in ids

    def test_filter_by_capabilities_empty(self, populated_registry):
        # No requirements → all available
        result = populated_registry.filter_by_capabilities([])
        assert len(result) == 3

    def test_filter_by_multiple_capabilities(self, populated_registry):
        result = populated_registry.filter_by_capabilities(
            [Capability.CODING, Capability.TOOL_CALLING]
        )
        ids = [m.id for m in result]
        assert "vllm-7b" in ids
        assert "llamacpp-8b" in ids
        assert "ollama-vision" not in ids

    def test_filter_by_classification(self, populated_registry):
        # INTERNAL data → needs model with max_classification >= INTERNAL
        # vllm-7b (CONFIDENTIAL >= INTERNAL) ✓
        # ollama-vision (INTERNAL >= INTERNAL) ✓
        # llamacpp-8b (PUBLIC < INTERNAL) ✗
        result = populated_registry.filter_by_classification(DataClassification.INTERNAL)
        ids = [m.id for m in result]
        assert "vllm-7b" in ids
        assert "ollama-vision" in ids
        assert "llamacpp-8b" not in ids
        assert len(result) == 2

    def test_filter_by_classification_restricted(self, populated_registry):
        # RESTRICTED data → needs model with max_classification >= RESTRICTED
        # None qualify (highest is CONFIDENTIAL)
        result = populated_registry.filter_by_classification(DataClassification.RESTRICTED)
        assert len(result) == 0

    def test_filter_by_classification_public(self, populated_registry):
        # PUBLIC data → needs model with max_classification >= PUBLIC
        # All models qualify (PUBLIC <= everything)
        result = populated_registry.filter_by_classification(DataClassification.PUBLIC)
        assert len(result) == 3

    def test_filter_by_classification_confidential(self, populated_registry):
        # CONFIDENTIAL data → needs model with max_classification >= CONFIDENTIAL
        # vllm-7b (CONFIDENTIAL) ✓, others ✗
        result = populated_registry.filter_by_classification(DataClassification.CONFIDENTIAL)
        ids = [m.id for m in result]
        assert "vllm-7b" in ids
        assert len(result) == 1
