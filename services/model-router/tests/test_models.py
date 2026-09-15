"""Unit tests for domain types (models.py)."""

import pytest
from pydantic import ValidationError

from app.models import (
    Capability,
    CircuitState,
    DataClassification,
    Model,
    ModelSelectionRequest,
    ModelSelectionResponse,
    Provider,
    _CLASSIFICATION_ORDER,
)


def _make_model(**overrides) -> Model:
    """Build a Model with sensible defaults, overridden by kwargs."""
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


class TestModel:
    def test_basic_creation(self):
        m = _make_model()
        assert m.id == "test-model"
        assert m.provider == Provider.VLLM
        assert m.is_available is True

    def test_display_name_fallback(self):
        m = _make_model(display_name=None)
        assert m.display == "test-model"

    def test_display_name_preferred(self):
        m = _make_model(display_name="Custom Name")
        assert m.display == "Custom Name"

    def test_negative_parameters_rejected(self):
        with pytest.raises(ValidationError):
            _make_model(total_parameters_billions=-1.0)

    def test_zero_context_window_rejected(self):
        with pytest.raises(ValidationError):
            _make_model(context_window=0)

    def test_active_parameters_optional(self):
        m = _make_model(active_parameters_billions=None)
        assert m.active_parameters_billions is None

    def test_moe_active_parameters(self):
        m = _make_model(
            total_parameters_billions=64.0,
            active_parameters_billions=8.0,
        )
        assert m.active_parameters_billions == 8.0

    def test_all_providers_accepted(self):
        for provider in Provider:
            m = _make_model(provider=provider)
            assert m.provider == provider

    def test_all_classifications_accepted(self):
        for cls in DataClassification:
            m = _make_model(max_classification=cls)
            assert m.max_classification == cls


class TestClassificationOrder:
    def test_ordering(self):
        assert _CLASSIFICATION_ORDER[DataClassification.PUBLIC] < _CLASSIFICATION_ORDER[DataClassification.INTERNAL]
        assert _CLASSIFICATION_ORDER[DataClassification.INTERNAL] < _CLASSIFICATION_ORDER[DataClassification.CONFIDENTIAL]
        assert _CLASSIFICATION_ORDER[DataClassification.CONFIDENTIAL] < _CLASSIFICATION_ORDER[DataClassification.RESTRICTED]


class TestModelSelectionRequest:
    def test_empty_request(self):
        req = ModelSelectionRequest()
        assert req.required_capabilities == []
        assert req.max_classification is None

    def test_with_capabilities(self):
        req = ModelSelectionRequest(
            required_capabilities=[Capability.CODING, Capability.TOOL_CALLING]
        )
        assert len(req.required_capabilities) == 2


class TestModelSelectionResponse:
    def test_default_fallback_chain(self):
        resp = ModelSelectionResponse(
            model=_make_model(),
            fallback_chain=[],
            reason="best_match",
        )
        assert resp.fallback_chain == []
        assert resp.reason == "best_match"


class TestCircuitState:
    def test_states(self):
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"
