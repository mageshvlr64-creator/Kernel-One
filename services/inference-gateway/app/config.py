"""Environment-based configuration for the Inference Gateway."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class GatewayConfig:
    """Immutable config loaded once at process start."""

    # Model-router endpoint (internal service call)
    model_router_url: str = field(
        default_factory=lambda: os.getenv("MODEL_ROUTER_URL", "http://localhost:8002")
    )
    model_router_timeout_seconds: float = field(
        default_factory=lambda: float(os.getenv("MODEL_ROUTER_TIMEOUT_SECONDS", "5"))
    )

    # Provider base URLs
    vllm_base_url: str = field(
        default_factory=lambda: os.getenv("VLLM_BASE_URL", "http://localhost:8000")
    )
    ollama_base_url: str = field(
        default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    )
    llamacpp_base_url: str = field(
        default_factory=lambda: os.getenv("LLAMACPP_BASE_URL", "http://localhost:8080")
    )

    # Timeout budgets per runtime/11_retry_policy.md model-inference row:
    # 30s text, 60s vision (CONFIG DEFAULT, not yet benchmarked)
    inference_timeout_text_seconds: float = field(
        default_factory=lambda: float(os.getenv("INFERENCE_TIMEOUT_TEXT_SECONDS", "30"))
    )
    inference_timeout_vision_seconds: float = field(
        default_factory=lambda: float(os.getenv("INFERENCE_TIMEOUT_VISION_SECONDS", "60"))
    )

    # Retry: 1 retry on MODEL_UNAVAILABLE / INFERENCE_TIMEOUT, fixed 500ms backoff
    max_retries: int = field(default_factory=lambda: int(os.getenv("INFERENCE_MAX_RETRIES", "1")))
    retry_backoff_seconds: float = field(
        default_factory=lambda: float(os.getenv("INFERENCE_RETRY_BACKOFF_SECONDS", "0.5"))
    )

    # Whether to walk the fallback chain when the primary model fails
    # (per features/02_model_router/09_fallback_routing.md)
    enable_fallback: bool = field(
        default_factory=lambda: os.getenv("INFERENCE_ENABLE_FALLBACK", "true").lower() == "true"
    )

    # Database (audit persistence; optional)
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", ""))

    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "info"))
