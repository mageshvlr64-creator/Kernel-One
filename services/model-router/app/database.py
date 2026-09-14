"""Async PostgreSQL repository for model-router state.

Stores:
- Model registry rows (synced from the registry file on startup)
- Audit events emitted by the router

DDL: infra/migrations/ (Character 1 owns infra/)
"""

from __future__ import annotations

import json
import logging
from typing import Optional

import asyncpg

from .models import AuditEvent, Model, Provider, DataClassification, Capability

logger = logging.getLogger(__name__)


class ModelRepository:
    """Async repository backed by asyncpg.

    Provides persistence for model registry state and audit events.
    On startup, ``init_schema()`` creates tables if they don't exist (for
    local dev / test bootstrapping); production uses forward-only migrations
    in infra/migrations/.
    """

    def __init__(self, pool: asyncpg.Pool) -> None:  # type: ignore[type-arg]
        self._pool = pool

    # ------------------------------------------------------------------
    # DDL (local/test bootstrap only — production uses migrations)
    # ------------------------------------------------------------------

    async def init_schema(self) -> None:
        """Create tables if they don't exist (for dev/test bootstrapping)."""
        async with self._pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS models (
                    id              TEXT PRIMARY KEY,
                    display_name    TEXT,
                    provider        TEXT NOT NULL,
                    total_parameters_billions REAL NOT NULL CHECK (total_parameters_billions >= 0),
                    active_parameters_billions REAL CHECK (active_parameters_billions >= 0),
                    quantization    TEXT,
                    context_window  INTEGER NOT NULL CHECK (context_window >= 1),
                    capabilities    TEXT[] NOT NULL DEFAULT '{}',
                    max_classification TEXT NOT NULL,
                    is_available    BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS model_audit_events (
                    id              BIGSERIAL PRIMARY KEY,
                    event_type      TEXT NOT NULL DEFAULT 'model_selection',
                    actor_id        TEXT,
                    model_id        TEXT,
                    provider        TEXT,
                    classification  TEXT,
                    result          TEXT NOT NULL,
                    error_code      TEXT,
                    details         TEXT,
                    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """)
            # Index for fast audit lookups by model
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_model
                ON model_audit_events (model_id, created_at DESC);
            """)
        logger.info("Model-router schema initialized")

    # ------------------------------------------------------------------
    # Model CRUD
    # ------------------------------------------------------------------

    async def upsert_model(self, model: Model) -> None:
        """Insert or update a model row."""
        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO models (
                    id, display_name, provider, total_parameters_billions,
                    active_parameters_billions, quantization, context_window,
                    capabilities, max_classification, is_available, updated_at
                ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,NOW())
                ON CONFLICT (id) DO UPDATE SET
                    display_name = EXCLUDED.display_name,
                    provider = EXCLUDED.provider,
                    total_parameters_billions = EXCLUDED.total_parameters_billions,
                    active_parameters_billions = EXCLUDED.active_parameters_billions,
                    quantization = EXCLUDED.quantization,
                    context_window = EXCLUDED.context_window,
                    capabilities = EXCLUDED.capabilities,
                    max_classification = EXCLUDED.max_classification,
                    is_available = EXCLUDED.is_available,
                    updated_at = NOW()
            """,
                model.id,
                model.display_name,
                model.provider.value,
                model.total_parameters_billions,
                model.active_parameters_billions,
                model.quantization,
                model.context_window,
                [c.value for c in model.capabilities],
                model.max_classification.value,
                model.is_available,
            )

    async def get_model(self, model_id: str) -> Optional[Model]:
        """Fetch a single model by ID."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM models WHERE id = $1", model_id
            )
        if row is None:
            return None
        return self._row_to_model(row)

    async def list_models(self) -> list[Model]:
        """Fetch all registered models."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM models ORDER BY id")
        return [self._row_to_model(r) for r in rows]

    async def update_availability(
        self, model_id: str, is_available: bool
    ) -> bool:
        """Update a model's availability. Returns False if not found."""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE models SET is_available = $1, updated_at = NOW() WHERE id = $2",
                is_available,
                model_id,
            )
        return result.endswith("UPDATE 1")

    async def delete_model(self, model_id: str) -> bool:
        """Remove a model. Returns False if not found."""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM models WHERE id = $1", model_id
            )
        return result.endswith("DELETE 1")

    # ------------------------------------------------------------------
    # Audit events
    # ------------------------------------------------------------------

    async def record_audit_event(self, event: AuditEvent) -> None:
        """Persist an audit event."""
        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO model_audit_events (
                    event_type, actor_id, model_id, provider,
                    classification, result, error_code, details
                ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
            """,
                event.event_type,
                event.actor_id,
                event.model_id,
                event.provider.value if event.provider else None,
                event.classification.value if event.classification else None,
                event.result,
                event.error_code,
                event.details,
            )

    async def get_audit_events(
        self,
        model_id: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        """Fetch recent audit events, optionally filtered by model_id."""
        async with self._pool.acquire() as conn:
            if model_id:
                rows = await conn.fetch(
                    """SELECT * FROM model_audit_events
                       WHERE model_id = $1
                       ORDER BY created_at DESC LIMIT $2""",
                    model_id,
                    limit,
                )
            else:
                rows = await conn.fetch(
                    """SELECT * FROM model_audit_events
                       ORDER BY created_at DESC LIMIT $1""",
                    limit,
                )
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_model(row: asyncpg.Record) -> Model:  # type: ignore[type-arg]
        """Map a database row to a Model domain object."""
        return Model(
            id=row["id"],
            display_name=row["display_name"],
            provider=Provider(row["provider"]),
            total_parameters_billions=row["total_parameters_billions"],
            active_parameters_billions=row["active_parameters_billions"],
            quantization=row["quantization"],
            context_window=row["context_window"],
            capabilities=[Capability(c) for c in row["capabilities"]],
            max_classification=DataClassification(row["max_classification"]),
            is_available=row["is_available"],
        )
