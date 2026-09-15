"""Service configuration.

Honors the canonical environment keys from docs/16_ENVIRONMENT_AND_CONFIGURATION.md that
this service consumes. Per that file's rule, no new configuration key is invented here:
the object-storage stub below uses a service-local development directory instead of a new
env var (see docs/20_DECISION_LOG.md DEC-023). When the real MinIO integration lands, the
canonical OBJECT_STORAGE_* keys take over and this stub is deleted.

Precedence follows docs/16: environment variable > schema-declared default. Security-relevant
keys never fall back silently — none are needed by this increment (no DB, no JWT verification
yet: auth is an explicit dev stub, see policy.py / DEC-023).
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("document_pipeline.config")

VALID_NETWORK_MODES = ("air_gapped", "restricted", "on_premise")
VALID_LOG_LEVELS = ("debug", "info", "warn", "error")


@dataclass(frozen=True)
class Settings:
    network_mode: str = "air_gapped"
    max_upload_size_bytes: int = 209_715_200  # MAX_UPLOAD_SIZE_BYTES default, docs/16
    log_level: str = "info"
    # Service-local dev directory for the object-storage STUB (not a production key).
    storage_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / ".local" / "object-storage")


def load_settings(environ: dict | None = None) -> Settings:
    env = os.environ if environ is None else environ

    network_mode = env.get("NETWORK_MODE", "air_gapped")
    if network_mode not in VALID_NETWORK_MODES:
        raise ValueError(
            f"NETWORK_MODE={network_mode!r} is not one of {VALID_NETWORK_MODES} "
            "(docs/16_ENVIRONMENT_AND_CONFIGURATION.md)"
        )

    log_level = env.get("LOG_LEVEL", "info").lower()
    if log_level not in VALID_LOG_LEVELS:
        raise ValueError(
            f"LOG_LEVEL={log_level!r} is not one of {VALID_LOG_LEVELS} "
            "(docs/16_ENVIRONMENT_AND_CONFIGURATION.md)"
        )

    raw_max = env.get("MAX_UPLOAD_SIZE_BYTES", "209715200")
    try:
        max_upload = int(raw_max)
    except ValueError as exc:
        raise ValueError(f"MAX_UPLOAD_SIZE_BYTES={raw_max!r} is not an integer") from exc
    if max_upload < 1:
        raise ValueError("MAX_UPLOAD_SIZE_BYTES must be >= 1")

    if "OBJECT_STORAGE_ENDPOINT" in env:
        # Fail loud, not silent (developer rule 7): the stub is NOT production storage.
        logger.warning(
            "OBJECT_STORAGE_ENDPOINT=%s is set but the object-storage STUB is active; "
            "it serves a local directory and will be replaced by the MinIO integration "
            "(DEC-023).",
            env["OBJECT_STORAGE_ENDPOINT"],
        )

    return Settings(
        network_mode=network_mode,
        max_upload_size_bytes=max_upload,
        log_level=log_level,
    )
