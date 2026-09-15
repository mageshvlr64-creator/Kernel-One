"""Async PostgreSQL repository for inference-gateway audit events."""

from __future__ import annotations

import logging
from typing import Optional

import asyncpg

logger = logging.getLogger(__name__)


class InferenceAuditRepository:
    """Persists audit events for inference calls.

    Table mirrors the model-router's audit schema so operators can query
    both with the same shape.
    """

    def __init__(self, pool: asyncpg.Pool) -> None:  # type: ignore[type-arg]
        self._pool = pool

    async def init_schema(self) -> None:
        """Create tables if they don't exist (dev/test bootstrap)."""
        async with self._pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS inference_audit_events (
                    id              BIGSERIAL PRIMARY KEY,
                    event_type      TEXT NOT NULL DEFAULT 'inference_call',
                    actor_id        TEXT,
                    model_id        TEXT,
                    provider        TEXT,
                    classification  TEXT,
                    result          TEXT NOT NULL,
                    error_code      TEXT,
                    details         TEXT,
                    latency_ms      REAL,
                    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_inference_audit_model
                ON inference_audit_events (model_id, created_at DESC);
            """)
        logger.info("Inference-gateway schema initialized")

    async def record(
        self,
        *,
        actor_id: Optional[str],
        model_id: Optional[str],
        provider: Optional[str],
        result: str,
        error_code: Optional[str] = None,
        details: Optional[str] = None,
        latency_ms: Optional[float] = None,
    ) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO inference_audit_events (
                    actor_id, model_id, provider, result, error_code, details, latency_ms
                ) VALUES ($1,$2,$3,$4,$5,$6,$7)
            """,
                actor_id,
                model_id,
                provider,
                result,
                error_code,
                details,
                latency_ms,
            )
