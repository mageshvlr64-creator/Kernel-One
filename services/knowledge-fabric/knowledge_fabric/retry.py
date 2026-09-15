"""Retry policy — docs/runtime/11_retry_policy.md (canonical, read-only).

knowledge-fabric's ops are classified per feature docs §18:
- indexing pipeline ops (document_store, normalization, chunking, embeddings, indexes):
  `document-processing`
- retrieval ops (hybrid_search, reranking, context_assembly, quality/failures reads):
  `interactive-read`

This module implements the canonical numbers as a tiny helper; the registry-based retry
classification is the same implementation document-pipeline uses (verified against
runtime/11 there), kept byte-compatible so the two services retry identically.
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
    RETRIEVAL_OPS = {
        "hybrid_search", "reranking", "context_assembly",
        "retrieval_quality", "retrieval_failures", "knowledge_overview",
    }
    return "interactive-read" if op in RETRIEVAL_OPS else "document-processing"


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
