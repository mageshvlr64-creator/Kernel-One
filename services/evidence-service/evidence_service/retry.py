"""Retry policy — docs/runtime/11_retry_policy.md (canonical, read-only).

Evidence feature docs §18 classify these ops as `interactive-read` (the p95
150ms budget in §23 is the interactive-citation-resolution path). Same canonical
numbers and helper shape as the sibling services, so retry behavior is uniform
across the platform.
"""
from __future__ import annotations

import time
from typing import Any, Callable, Tuple

# Canonical classes (runtime/11_retry_policy.md): (max_attempts, base_backoff_seconds)
CLASSES: dict = {
    "document-processing": (3, 2.0),
    "interactive-read": (2, 0.5),
}

BACKOFF_SECONDS = 0.0  # tests set >0 to exercise sleeping paths


def classify(op: str) -> str:
    # All ten evidence ops are interactive reads/writes at human-wait latency.
    return "interactive-read"


def run_with_retry(fn: Callable[[], Any], op: str,
                   retryable: Tuple[str, ...] = ("DEPENDENCY_UNAVAILABLE",
                                                 "RAG_INDEX_UNAVAILABLE")) -> Any:
    """Run fn(); retry only registry-retryable failures per the canonical class."""
    max_attempts, base = CLASSES[classify(op)]
    last: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 — translated by the ops layer
            code = getattr(exc, "code", None)
            if code not in retryable or attempt == max_attempts:
                raise
            last = exc
            if BACKOFF_SECONDS:
                time.sleep(base * (2 ** (attempt - 1)) * BACKOFF_SECONDS)
    raise last  # pragma: no cover — loop always returns or raises
