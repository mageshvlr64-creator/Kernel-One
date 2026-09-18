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


class TestCircuitBreakerFreshBoot:
    """Regression tests for the monotonic-clock sentinel bug caught on CI.

    time.monotonic() reads seconds since boot, so on a freshly provisioned
    host a real timestamp can sit below the failure window, and backdating
    past the window crosses zero into negative territory. The pre-fix code
    used ``last_failure_time > 0.0`` as the never-failed sentinel, which
    misclassified such a negative timestamp as never-failed and skipped the
    window reset (CI: breaker stuck OPEN). ``None`` now means never-failed;
    these tests pin that behavior under a small clock reading.
    """

    def test_never_failed_uses_none_sentinel(self):
        cb = _make_breaker()
        assert cb.get_state("model-a") == CircuitState.CLOSED  # materializes state
        assert cb._breakers["model-a"].last_failure_time is None
        cb.record_failure("model-a")
        assert cb._breakers["model-a"].last_failure_time is not None

    def test_window_reset_fires_with_small_monotonic_readings(self):
        # Simulate a host ~30s past boot: patching the clock makes the 31s-
        # backdated failure land before boot (negative). The old ``> 0.0``
        # guard skipped the reset and tripped the breaker here; the fixed
        # code must forgive the out-of-window failures regardless of sign.
        cb = _make_breaker(failure_threshold=3, window_seconds=10.0)
        cb.record_failure("model-a")
        cb.record_failure("model-a")
        assert cb.get_state("model-a") == CircuitState.CLOSED

        cb._breakers["model-a"].last_failure_time = 30.0 - 31.0
        with patch("app.circuit_breaker.time.monotonic", return_value=30.0):
            cb.record_failure("model-a")
        assert cb.get_state("model-a") == CircuitState.CLOSED

        with patch("app.circuit_breaker.time.monotonic", return_value=30.5):
            cb.record_failure("model-a")
            cb.record_failure("model-a")
        assert cb.get_state("model-a") == CircuitState.OPEN
