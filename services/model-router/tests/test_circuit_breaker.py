"""Unit tests for the circuit breaker."""

import time
from unittest.mock import patch

from app.circuit_breaker import CircuitBreaker
from app.models import CircuitState


def _make_breaker(
    failure_threshold: int = 3,
    window_seconds: float = 10.0,
    half_open_probe_seconds: float = 2.0,
) -> CircuitBreaker:
    return CircuitBreaker(
        failure_threshold=failure_threshold,
        window_seconds=window_seconds,
        half_open_probe_seconds=half_open_probe_seconds,
    )


class TestCircuitBreakerClosed:
    def test_starts_closed(self):
        cb = _make_breaker()
        assert cb.get_state("model-a") == CircuitState.CLOSED

    def test_allows_requests_when_closed(self):
        cb = _make_breaker()
        assert cb.allow_request("model-a") is True

    def test_recording_success_resets_count(self):
        cb = _make_breaker(failure_threshold=3)
        cb.record_failure("model-a")
        cb.record_failure("model-a")
        cb.record_success("model-a")
        # Should be back to CLOSED with 0 failures
        assert cb.get_state("model-a") == CircuitState.CLOSED
        assert cb.allow_request("model-a") is True


class TestCircuitBreakerTrips:
    def test_trips_after_threshold(self):
        cb = _make_breaker(failure_threshold=3)
        cb.record_failure("model-a")
        cb.record_failure("model-a")
        cb.record_failure("model-a")
        assert cb.get_state("model-a") == CircuitState.OPEN

    def test_blocks_when_open(self):
        cb = _make_breaker(failure_threshold=2)
        cb.record_failure("model-a")
        cb.record_failure("model-a")
        assert cb.allow_request("model-a") is False

    def test_different_models_independent(self):
        cb = _make_breaker(failure_threshold=2)
        cb.record_failure("model-a")
        cb.record_failure("model-a")
        # model-a is open, model-b is still closed
        assert cb.allow_request("model-a") is False
        assert cb.allow_request("model-b") is True

    def test_success_during_half_open_resets(self):
        cb = _make_breaker(failure_threshold=2, half_open_probe_seconds=0.01)
        cb.record_failure("model-a")
        cb.record_failure("model-a")
        assert cb.get_state("model-a") == CircuitState.OPEN

        # Wait for half-open
        time.sleep(0.02)
        assert cb.allow_request("model-a") is True
        assert cb.get_state("model-a") == CircuitState.HALF_OPEN

        cb.record_success("model-a")
        assert cb.get_state("model-a") == CircuitState.CLOSED

    def test_failure_during_half_open_reopens(self):
        cb = _make_breaker(failure_threshold=2, half_open_probe_seconds=0.01)
        cb.record_failure("model-a")
        cb.record_failure("model-a")

        time.sleep(0.02)
        assert cb.allow_request("model-a") is True  # enters half-open

        cb.record_failure("model-a")
        assert cb.get_state("model-a") == CircuitState.OPEN


class TestCircuitBreakerReset:
    def test_manual_reset(self):
        cb = _make_breaker(failure_threshold=1)
        cb.record_failure("model-a")
        assert cb.get_state("model-a") == CircuitState.OPEN

        cb.reset("model-a")
        assert cb.get_state("model-a") == CircuitState.CLOSED
        assert cb.allow_request("model-a") is True
