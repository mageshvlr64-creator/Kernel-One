"""Environment-based configuration for the Model Router.

All keys are defined here; no feature document defines its own config key
without adding it here first per docs/16_ENVIRONMENT_AND_CONFIGURATION.md.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModelRouterConfig:
    """Immutable config loaded once at process start.

    Precedence: env var > .env file > schema-declared default.
    """

    # Provider base URLs (injected per deployment)
    vllm_base_url: str = field(
        default_factory=lambda: os.getenv("VLLM_BASE_URL", "http://localhost:8000")
    )
    ollama_base_url: str = field(
        default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    )
    llamacpp_base_url: str = field(
        default_factory=lambda: os.getenv("LLAMACPP_BASE_URL", "http://localhost:8080")
    )

    # Model registry path — required per 16_ENVIRONMENT_AND_CONFIGURATION.md
    model_registry_path: str = field(
        default_factory=lambda: os.getenv("MODEL_REGISTRY_PATH", "")
    )

    # Health polling
    health_poll_interval_seconds: float = field(
        default_factory=lambda: float(os.getenv("HEALTH_POLL_INTERVAL_SECONDS", "30"))
    )
    health_check_timeout_seconds: float = field(
        default_factory=lambda: float(os.getenv("HEALTH_CHECK_TIMEOUT_SECONDS", "5"))
    )

    # Circuit breaker defaults (per runtime/11_retry_policy.md "model-inference")
    circuit_breaker_failure_threshold: int = field(
        default_factory=lambda: int(
            os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5")
        )
    )
    circuit_breaker_window_seconds: float = field(
        default_factory=lambda: float(
            os.getenv("CIRCUIT_BREAKER_WINDOW_SECONDS", "60")
        )
    )
    circuit_breaker_half_open_probe_seconds: float = field(
        default_factory=lambda: float(
            os.getenv("CIRCUIT_BREAKER_HALF_OPEN_PROBE_SECONDS", "15")
        )
    )

    # Model inference timeout (per runtime/11_retry_policy.md)
    inference_timeout_text_seconds: float = field(
        default_factory=lambda: float(
            os.getenv("INFERENCE_TIMEOUT_TEXT_SECONDS", "30")
        )
    )
    inference_timeout_vision_seconds: float = field(
        default_factory=lambda: float(
            os.getenv("INFERENCE_TIMEOUT_VISION_SECONDS", "60")
        )
    )

    # Database
    database_url: str = field(
        default_factory=lambda: os.getenv("DATABASE_URL", "")
    )

    # Logging
    log_level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "info")
    )
