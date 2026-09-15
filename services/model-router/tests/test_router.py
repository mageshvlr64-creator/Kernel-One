"""Unit tests for the model selection router."""

import pytest

from app.circuit_breaker import CircuitBreaker
from app.config import ModelRouterConfig
from app.models import (
    Capability,
    DataClassification,
    Model,
    ModelSelectionRequest,
    Provider,
)
from app.registry import ModelRegistry
from app.router import ModelRouter


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
def setup():
    """Shared setup for router tests."""
    config = ModelRouterConfig(model_registry_path="")
    registry = ModelRegistry(config)
    circuit_breaker = CircuitBreaker(
        failure_threshold=3, window_seconds=60.0, half_open_probe_seconds=0.01
    )
    router = ModelRouter(registry, circuit_breaker)
    return registry, circuit_breaker, router


class TestSelectBasic:
    def test_select_with_single_model(self, setup):
        registry, _, router = setup
        registry.register_model(_make_model(id="only-model"))

        response, event = router.select(ModelSelectionRequest())
        assert response is not None
        assert response.model.id == "only-model"
        assert event.result == "success"
        assert event.model_id == "only-model"

    def test_select_no_models_returns_error(self, setup):
        _, _, router = setup

        response, event = router.select(ModelSelectionRequest())
        assert response is None
        assert event.result == "error"
        assert event.error_code == "MODEL_UNAVAILABLE"

    def test_select_respects_capability_filter(self, setup):
        registry, _, router = setup
        registry.register_model(_make_model(
            id="coding-model",
            capabilities=[Capability.CODING],
        ))
        registry.register_model(_make_model(
            id="vision-model",
            display_name="Vision",
            capabilities=[Capability.VISION],
        ))

        response, _ = router.select(
            ModelSelectionRequest(required_capabilities=[Capability.VISION])
        )
        assert response is not None
        assert response.model.id == "vision-model"

    def test_select_respects_classification(self, setup):
        registry, _, router = setup
        registry.register_model(_make_model(
            id="public-model",
            max_classification=DataClassification.PUBLIC,
        ))
        registry.register_model(_make_model(
            id="restricted-model",
            display_name="Restricted",
            total_parameters_billions=70.0,
            max_classification=DataClassification.RESTRICTED,
        ))

        # PUBLIC data → both models qualify; smaller one (public-model) preferred
        response, _ = router.select(
            ModelSelectionRequest(max_classification=DataClassification.PUBLIC)
        )
        assert response is not None
        assert response.model.id == "public-model"

    def test_select_respects_classification_filters_out_unqualified(self, setup):
        registry, _, router = setup
        registry.register_model(_make_model(
            id="public-model",
            max_classification=DataClassification.PUBLIC,
        ))
        registry.register_model(_make_model(
            id="restricted-model",
            display_name="Restricted",
            max_classification=DataClassification.RESTRICTED,
        ))

        # CONFIDENTIAL data → only restricted-model qualifies
        response, _ = router.select(
            ModelSelectionRequest(max_classification=DataClassification.CONFIDENTIAL)
        )
        assert response is not None
        assert response.model.id == "restricted-model"

    def test_select_respects_max_parameters(self, setup):
        registry, _, router = setup
        registry.register_model(_make_model(
            id="small-model", total_parameters_billions=3.0,
        ))
        registry.register_model(_make_model(
            id="large-model", display_name="Large",
            total_parameters_billions=70.0,
        ))

        response, _ = router.select(
            ModelSelectionRequest(max_parameters_billions=10.0)
        )
        assert response is not None
        assert response.model.id == "small-model"

    def test_select_respects_min_context_window(self, setup):
        registry, _, router = setup
        registry.register_model(_make_model(
            id="short-ctx", context_window=4096,
        ))
        registry.register_model(_make_model(
            id="long-ctx", display_name="Long",
            context_window=128000,
        ))

        response, _ = router.select(
            ModelSelectionRequest(min_context_window=8192)
        )
        assert response is not None
        assert response.model.id == "long-ctx"


class TestRanking:
    def test_preferred_provider_first(self, setup):
        registry, _, router = setup
        registry.register_model(_make_model(
            id="ollama-model", provider=Provider.OLLAMA,
            total_parameters_billions=7.0,
        ))
        registry.register_model(_make_model(
            id="vllm-model", provider=Provider.VLLM,
            total_parameters_billions=7.0,
        ))

        response, _ = router.select(
            ModelSelectionRequest(preferred_provider=Provider.OLLAMA)
        )
        assert response is not None
        assert response.model.id == "ollama-model"

    def test_smaller_model_preferred(self, setup):
        registry, _, router = setup
        registry.register_model(_make_model(
            id="big-model", total_parameters_billions=70.0,
        ))
        registry.register_model(_make_model(
            id="small-model", display_name="Small",
            total_parameters_billions=3.0,
        ))

        response, _ = router.select(ModelSelectionRequest())
        assert response is not None
        assert response.model.id == "small-model"

    def test_fallback_chain_populated(self, setup):
        registry, _, router = setup
        registry.register_model(_make_model(id="model-a"))
        registry.register_model(_make_model(
            id="model-b", display_name="B",
        ))

        response, _ = router.select(ModelSelectionRequest())
        assert response is not None
        assert len(response.fallback_chain) == 1  # 1 other model


class TestCircuitBreakerFallback:
    def test_skips_broken_model(self, setup):
        registry, cb, router = setup
        registry.register_model(_make_model(id="broken-model"))
        registry.register_model(_make_model(
            id="healthy-model", display_name="Healthy",
        ))

        # Trip the breaker for "broken-model"
        cb.record_failure("broken-model")
        cb.record_failure("broken-model")
        cb.record_failure("broken-model")

        response, event = router.select(ModelSelectionRequest())
        assert response is not None
        assert response.model.id == "healthy-model"
        assert "broken-model" in response.fallback_chain

    def test_all_broken_returns_error(self, setup):
        registry, cb, router = setup
        registry.register_model(_make_model(id="model-a"))
        registry.register_model(_make_model(
            id="model-b", display_name="B",
        ))

        cb.record_failure("model-a")
        cb.record_failure("model-a")
        cb.record_failure("model-a")
        cb.record_failure("model-b")
        cb.record_failure("model-b")
        cb.record_failure("model-b")

        response, event = router.select(ModelSelectionRequest())
        assert response is None
        assert event.result == "error"


class TestReportResult:
    def test_report_success_resets_breaker(self, setup):
        registry, cb, router = setup
        registry.register_model(_make_model(id="model-a"))
        registry.register_model(_make_model(
            id="model-b", display_name="B",
        ))

        # Partially trip model-a
        cb.record_failure("model-a")
        cb.record_failure("model-a")
        # Still under threshold (3)

        # Report success → resets
        router.report_success("model-a")
        assert cb.get_state("model-a").value == "closed"

    def test_report_failure_trips_breaker(self, setup):
        registry, cb, router = setup
        registry.register_model(_make_model(id="model-a"))

        router.report_failure("model-a")
        router.report_failure("model-a")
        router.report_failure("model-a")
        assert cb.get_state("model-a").value == "open"
