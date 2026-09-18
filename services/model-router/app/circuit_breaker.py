"""Per-model circuit breaker.

Implements the circuit-breaker pattern per runtime/11_retry_policy.md:
- CLOSED: normal operation, failures counted
- OPEN: calls fail immediately with MODEL_UNAVAILABLE
- HALF_OPEN: one probe call allowed; success → CLOSED, failure → OPEN

Tracked per model ID (not globally) per rule 3 of runtime/11_retry_policy.md.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from .models import CircuitState


@dataclass
class _ModelBreaker:
    """Internal state for a single model's circuit breaker."""

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    # None = never failed. A monotonic-clock timestamp of 0.0 (or any small
    # value) cannot act as the "no failure yet" sentinel: on a freshly booted
    # host monotonic() may read below the window itself, which would make a
    # real timestamp indistinguishable from "never" (CI-caught bug).
    last_failure_time: Optional[float] = None
    # None = never opened. Same sentinel convention as last_failure_time:
    # a small monotonic reading on a freshly booted host must never be
    # mistaken for "already open".
    opened_at: Optional[float] = None


class CircuitBreaker:
    """Per-model circuit breaker with configurable thresholds.

    Thresholds come from runtime/11_retry_policy.md "model-inference" row:
    open after 5 consecutive failures in 60s, half-open probe every 15s.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        window_seconds: float = 60.0,
        half_open_probe_seconds: float = 15.0,
    ) -> None:
        self._failure_threshold = failure_threshold
        self._window_seconds = window_seconds
        self._half_open_probe_seconds = half_open_probe_seconds
        self._breakers: dict[str, _ModelBreaker] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def allow_request(self, model_id: str) -> bool:
        """Return True if a request to *model_id* should proceed."""
        breaker = self._get(model_id)
        now = time.monotonic()

        if breaker.state == CircuitState.CLOSED:
            return True

        if breaker.state == CircuitState.OPEN:
            # Transition to HALF_OPEN after the probe window elapses
            if (
                breaker.opened_at is not None
                and now - breaker.opened_at >= self._half_open_probe_seconds
            ):
                breaker.state = CircuitState.HALF_OPEN
                return True
            return False

        # HALF_OPEN — exactly one probe allowed at a time
        return True

    def record_success(self, model_id: str) -> None:
        """Record a successful call — reset to CLOSED."""
        breaker = self._get(model_id)
        breaker.failure_count = 0
        breaker.state = CircuitState.CLOSED

    def record_failure(self, model_id: str) -> None:
        """Record a failed call — may trip the breaker to OPEN.

        Counts consecutive failures within the sliding window: a failure that
        arrives after ``window_seconds`` of quiet resets the counter first,
        so the breaker opens on N failures *in* the window (per
        runtime/11_retry_policy.md), not on N failures ever.
        """
        breaker = self._get(model_id)
        now = time.monotonic()

        if breaker.state == CircuitState.HALF_OPEN:
            # Probe failed — re-open
            breaker.last_failure_time = now
            breaker.state = CircuitState.OPEN
            breaker.opened_at = now
            return

        # CLOSED — accumulate failures
        # Reset counter if the previous failure is outside the window
        if (
            breaker.last_failure_time is not None
            and now - breaker.last_failure_time > self._window_seconds
        ):
            breaker.failure_count = 0

        breaker.last_failure_time = now
        breaker.failure_count += 1
        if breaker.failure_count >= self._failure_threshold:
            breaker.state = CircuitState.OPEN
            breaker.opened_at = now

    def get_state(self, model_id: str) -> CircuitState:
        """Return the current state for *model_id*."""
        return self._get(model_id).state

    def reset(self, model_id: str) -> None:
        """Manually reset a model's breaker to CLOSED."""
        breaker = self._get(model_id)
        breaker.state = CircuitState.CLOSED
        breaker.failure_count = 0

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get(self, model_id: str) -> _ModelBreaker:
        if model_id not in self._breakers:
            self._breakers[model_id] = _ModelBreaker()
        return self._breakers[model_id]
