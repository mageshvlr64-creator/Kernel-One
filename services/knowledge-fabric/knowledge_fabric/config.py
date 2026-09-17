"""Service settings — canonical env keys per docs/16_ENVIRONMENT_AND_CONFIGURATION.md.

Unknown env keys are ignored (fail-open config like document-pipeline's); every value has
a spec-derived default so the service boots with no environment at all.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name, "")
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name, "")
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@dataclass
class Settings:
    # Dev actor tokens (DEC-023 pattern; real authn replaces resolve_actor).
    dev_actor_tokens: dict = field(default_factory=lambda: {
        "dev-token-administrator": "Administrator",
        "dev-token-security-officer": "Security Officer",
        "dev-token-operator": "Operator",
        "dev-token-analyst": "Analyst",
        "dev-token-restricted": "Restricted User",
        "dev-token-auditor": "Auditor",
    })

    # Chunking window (features/13 §04: CONFIG DEFAULT 200-800 tokens per
    # domain/07_knowledge_model.md). Approximated with characters (4 chars/token).
    chunk_min_chars: int = field(default_factory=lambda: _int_env("KF_CHUNK_MIN_CHARS", 800))
    chunk_max_chars: int = field(default_factory=lambda: _int_env("KF_CHUNK_MAX_CHARS", 3200))

    # Embedding dimension — fixed by the configured embedding model (schemas/08,
    # domain/07: vector(768)).
    embedding_dim: int = field(default_factory=lambda: _int_env("KF_EMBEDDING_DIM", 768))

    # Retrieval knobs (features/13 §09/§10: top-k candidate pool and final results).
    retrieval_candidates: int = field(default_factory=lambda: _int_env("KF_RETRIEVAL_CANDIDATES", 50))
    retrieval_top_k: int = field(default_factory=lambda: _int_env("KF_RETRIEVAL_TOP_K", 5))

    # Index readiness gate — minimum chunks before INDEXING -> READY succeeds.
    min_chunks_for_ready: int = field(default_factory=lambda: _int_env("KF_MIN_CHUNKS", 1))


def load_settings() -> Settings:
    return Settings()
