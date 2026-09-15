"""Retry policy bindings — docs/runtime/11_retry_policy.md (canonical, read-only).

This feature's operations are classified ``document-processing``. The values below are
copied verbatim from the canonical table; no local numbers are invented (developer rule 3).
Provenance label per the canonical file: CONFIG DEFAULT.
"""
from __future__ import annotations

import time
from typing import Callable, TypeVar

from .errors import RegistryError

# docs/runtime/11_retry_policy.md — class `document-processing`
TIMEOUT_SECONDS = 120          # per document; covers 50-page CPU OCR on PROFILE-A
MAX_RETRIES = 1
RETRYABLE_CODES = ("DEPENDENCY_UNAVAILABLE", "RAG_INDEX_UNAVAILABLE")
BACKOFF_SECONDS = 2.0          # fixed
MAX_BACKOFF_SECONDS = 2.0
CIRCUIT_BREAKER = "open after 5 consecutive failures in 5 minutes"

T = TypeVar("T")


def is_retryable(err: RegistryError) -> bool:
    return err.code in RETRYABLE_CODES


def run_with_retry(
    operation: Callable[[], T],
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Run `operation` applying the canonical retry rule.

    Rule 1 of docs/runtime/11_retry_policy.md: retry only the codes listed under
    "Retryable on", never 4xx validation/authorization errors. Max retries: 1,
    fixed 2s backoff.
    """
    try:
        return operation()
    except RegistryError as first:
        if not is_retryable(first) or MAX_RETRIES < 1:
            raise
        sleep(BACKOFF_SECONDS)
        try:
            return operation()
        except RegistryError:
            # Surface the most recent failure; the registry entry carries operator detail.
            raise
