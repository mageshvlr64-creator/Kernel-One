"""Service settings — canonical env keys per docs/16_ENVIRONMENT_AND_CONFIGURATION.md.

Every value has a spec-derived default so the service boots with no environment;
unknown env keys are ignored (same fail-open config posture as the sibling
services, documented in DEC-023).
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
    # Dev actor tokens (DEC-023 pattern; identity-service replaces resolve_actor).
    dev_actor_tokens: dict = field(default_factory=lambda: {
        "dev-token-administrator": "Administrator",
        "dev-token-security-officer": "Security Officer",
        "dev-token-operator": "Operator",
        "dev-token-analyst": "Analyst",
        "dev-token-restricted": "Restricted User",
        "dev-token-auditor": "Auditor",
    })

    # Claim-extraction segmentation ceiling (op 02). CONFIG DEFAULT: extraction is
    # a bounded heuristic, not an open-ended parse.
    claim_max_chars: int = field(default_factory=lambda: _int_env("EV_CLAIM_MAX_CHARS", 8000))

    # Claims above this many chars cannot carry a citation span at all (op 05).
    claim_span_hard_limit: int = field(default_factory=lambda: _int_env("EV_CLAIM_SPAN_LIMIT", 65536))

    # Chain resolution: how many ancestor hops MAXIMUM before the chain is declared
    # cyclic/broken (op 06). CONFIG DEFAULT, defensive against bad upstream data.
    source_chain_max_depth: int = field(default_factory=lambda: _int_env("EV_CHAIN_MAX_DEPTH", 16))

    # Confidence axes (op 08): coverage ratio at/above which coverage reads High,
    # and the unsupported-claim ratio at/above which an answer is flagged.
    coverage_high_ratio: float = field(default_factory=lambda: _float_env("EV_COVERAGE_HIGH", 0.9))
    coverage_partial_ratio: float = field(default_factory=lambda: _float_env("EV_COVERAGE_PARTIAL", 0.5))
    unsupported_flag_ratio: float = field(default_factory=lambda: _float_env("EV_UNSUPPORTED_RATIO", 0.2))

    # Unsupported-claim detection requires evidence rows to at least share the
    # answer's task before counting as support (op 09).
    min_supporting_evidence: int = field(default_factory=lambda: _int_env("EV_MIN_SUPPORT", 1))

    # Cross-service enrichment (Character-3 side of the industrial-service
    # boundary): evidence-service ingest calls /internal/resolve-tag and
    # /internal/validate-finding during op 01 when the payload carries the
    # optional equipment_tag/finding extensions. Kept explicit and optional —
    # the endpoints stay additive; a payload without them never touches the
    # dependency.
    industrial_base_url: str = field(default_factory=lambda: os.getenv(
        "EV_INDUSTRIAL_BASE_URL", "http://127.0.0.1:8005"))
    industrial_timeout_seconds: float = field(default_factory=lambda: _float_env(
        "EV_INDUSTRIAL_TIMEOUT_SECONDS", 5.0))


def load_settings() -> Settings:
    return Settings()
