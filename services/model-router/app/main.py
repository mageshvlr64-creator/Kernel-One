"""Model Router service — FastAPI application.

Routes:
  GET  /api/v1/models              — list all registered models
  GET  /api/v1/models/{id}         — get a single model by ID
  POST /api/v1/models/select       — select the best model for a request
  POST /api/v1/models              — register or update a model
  DELETE /api/v1/models/{id}       — unregister a model
  PATCH /api/v1/models/{id}/availability — set model availability
  GET  /api/v1/models/health       — health status for all models
  GET  /api/v1/models/{id}/health  — health status for one model
  GET  /api/v1/audit               — recent audit events
  GET  /healthz                    — liveness probe
  GET  /readyz                     — readiness probe (checks DB + registry)

Every mutating route emits an AuditEvent (developer rule 4).
All permission checks fail closed (developer rule 11).
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Optional

import asyncpg
from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

from .config import ModelRouterConfig
from .circuit_breaker import CircuitBreaker
from .database import ModelRepository
from .models import (
    AuditEvent,
    DataClassification,
    Model,
    ModelHealth,
    ModelSelectionRequest,
    ModelSelectionResponse,
    Provider,
)
from .registry import ModelRegistry, RegistryConfigError
from .router import ModelRouter

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared state (initialized at startup)
# ---------------------------------------------------------------------------
_config = ModelRouterConfig()
_circuit_breaker = CircuitBreaker(
    failure_threshold=_config.circuit_breaker_failure_threshold,
    window_seconds=_config.circuit_breaker_window_seconds,
    half_open_probe_seconds=_config.circuit_breaker_half_open_probe_seconds,
)
_registry = ModelRegistry(_config)
_model_router = ModelRouter(_registry, _circuit_breaker)
_db_pool: Optional[asyncpg.Pool] = None  # type: ignore[type-arg]
_repo: Optional[ModelRepository] = None


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    global _db_pool, _repo

    # Load model registry from config file. A malformed catalog is a boot
    # failure, not a warning: the service must not come up half-configured.
    try:
        await _registry.load()
    except RegistryConfigError as exc:
        logger.critical(
            "MODEL ROUTER BOOT FAILURE — model registry %s is invalid, "
            "refusing to start:\n%s",
            _config.model_registry_path,
            exc,
        )
        raise SystemExit(f"model-router: invalid model registry: {exc}") from exc

    # Connect to database (if configured)
    if _config.database_url:
        try:
            _db_pool = await asyncpg.create_pool(
                _config.database_url, min_size=1, max_size=5
            )
            _repo = ModelRepository(_db_pool)
            await _repo.init_schema()

            # Sync in-memory registry → database
            for model in _registry.list_all():
                await _repo.upsert_model(model)

            logger.info("Connected to PostgreSQL")
        except Exception as exc:
            logger.error("Failed to connect to database: %s", exc)
            # Service can still run without DB for read-only model selection
    else:
        logger.warning("DATABASE_URL not set — running without persistence")

    # Start health polling
    await _registry.start_health_polling()

    yield

    # Shutdown
    await _registry.stop_health_polling()
    if _db_pool is not None:
        await _db_pool.close()


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Model Router",
    description=(
        "Routes inference requests to the appropriate model/provider "
        "with fallback and circuit-breaking per runtime/11_retry_policy.md"
    ),
    version="0.1.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Request / response helpers
# ---------------------------------------------------------------------------

class AvailabilityRequest(BaseModel):
    is_available: bool


class ModelCreateRequest(BaseModel):
    """Body for POST /api/v1/models (register or update).

    Field constraints mirror app.models.Model so invalid registrations are
    rejected by request validation (422) instead of failing later.
    """

    id: str
    display_name: Optional[str] = None
    provider: Provider
    total_parameters_billions: float = Field(ge=0)
    active_parameters_billions: Optional[float] = Field(default=None, ge=0)
    quantization: Optional[str] = None
    context_window: int = Field(ge=1)
    capabilities: list[str] = []
    max_classification: DataClassification
    is_available: bool = True


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[str] = None


# ---------------------------------------------------------------------------
# Permission helper
# ---------------------------------------------------------------------------

# Required roles per operation — fails closed (developer rule 11)
_READ_ROLES = {"Operator", "Engineer", "Administrator", "Auditor"}
_WRITE_ROLES = {"Administrator"}
_ADMIN_ROLES = {"Administrator"}


def _check_roles(
    x_roles: str = Header(default="", alias="x-roles"),
    required: set[str] = _READ_ROLES,
) -> list[str]:
    """Validate caller has at least one required role.

    Fails closed: if no roles header is present, deny access.
    """
    if not x_roles:
        raise HTTPException(status_code=403, detail="POLICY_DENIED: no roles provided")
    roles = [r.strip() for r in x_roles.split(",") if r.strip()]
    if not any(r in required for r in roles):
        raise HTTPException(status_code=403, detail="POLICY_DENIED: insufficient permissions")
    return roles


async def _emit_audit(event: AuditEvent) -> None:
    """Persist audit event if DB is available."""
    if _repo is not None:
        try:
            await _repo.record_audit_event(event)
        except Exception as exc:
            logger.error("Failed to record audit event: %s", exc)


# ---------------------------------------------------------------------------
# Routes — Models
# ---------------------------------------------------------------------------

@app.get("/api/v1/models", response_model=list[Model])
async def list_models(x_roles: str = Header(default="", alias="x-roles")):
    """List all registered models."""
    _check_roles(x_roles, _READ_ROLES)
    return _registry.list_all()


@app.get("/api/v1/models/{model_id}", response_model=Model)
async def get_model(model_id: str, x_roles: str = Header(default="", alias="x-roles")):
    """Get a single model by ID."""
    _check_roles(x_roles, _READ_ROLES)
    model = _registry.get(model_id)
    if model is None:
        raise HTTPException(status_code=404, detail="FILE_NOT_FOUND")
    return model


@app.post("/api/v1/models/select", response_model=ModelSelectionResponse)
async def select_model(
    request: ModelSelectionRequest,
    x_roles: str = Header(default="", alias="x-roles"),
):
    """Select the best model for a given request.

    Returns the selected model with a fallback chain.
    Emits an audit event on every call (success or failure).
    """
    roles = _check_roles(x_roles, _READ_ROLES)

    # Determine actor_id from roles (simplified — real JWT would extract subject)
    actor_id = roles[0] if roles else None

    response, event = _model_router.select(request, actor_id=actor_id)

    # Persist audit event
    await _emit_audit(event)

    if response is None:
        raise HTTPException(
            status_code=503,
            detail="MODEL_UNAVAILABLE: " + (event.details or "no model matches"),
        )
    return response


@app.post("/api/v1/models", response_model=Model, status_code=201)
async def create_model(
    body: ModelCreateRequest,
    x_roles: str = Header(default="", alias="x-roles"),
):
    """Register or update a model in the registry."""
    _check_roles(x_roles, _WRITE_ROLES)

    from .models import Capability as Cap

    try:
        capabilities = [Cap(c) for c in body.capabilities]
    except ValueError as exc:
        # Unknown capability tag: a client error (422), never a 500.
        raise HTTPException(
            status_code=422,
            detail=f"INVALID_REQUEST: unknown capability in 'capabilities': {exc}",
        ) from exc

    model = Model(
        id=body.id,
        display_name=body.display_name,
        provider=body.provider,
        total_parameters_billions=body.total_parameters_billions,
        active_parameters_billions=body.active_parameters_billions,
        quantization=body.quantization,
        context_window=body.context_window,
        capabilities=capabilities,
        max_classification=body.max_classification,
        is_available=body.is_available,
    )

    _registry.register_model(model)

    if _repo is not None:
        await _repo.upsert_model(model)

    await _emit_audit(AuditEvent(
        event_type="model_registered",
        model_id=model.id,
        provider=model.provider,
        result="success",
    ))

    return model


@app.delete("/api/v1/models/{model_id}", status_code=204)
async def delete_model(model_id: str, x_roles: str = Header(default="", alias="x-roles")):
    """Unregister a model from the registry."""
    _check_roles(x_roles, _WRITE_ROLES)

    removed = _registry.unregister_model(model_id)
    if not removed:
        raise HTTPException(status_code=404, detail="FILE_NOT_FOUND")

    if _repo is not None:
        await _repo.delete_model(model_id)

    await _emit_audit(AuditEvent(
        event_type="model_unregistered",
        model_id=model_id,
        result="success",
    ))


@app.patch("/api/v1/models/{model_id}/availability", response_model=Model)
async def set_availability(
    model_id: str,
    body: AvailabilityRequest,
    x_roles: str = Header(default="", alias="x-roles"),
):
    """Set a model's availability (admin toggle)."""
    _check_roles(x_roles, _WRITE_ROLES)

    updated = _registry.set_available(model_id, body.is_available)
    if not updated:
        raise HTTPException(status_code=404, detail="FILE_NOT_FOUND")

    if _repo is not None:
        await _repo.update_availability(model_id, body.is_available)

    model = _registry.get(model_id)

    await _emit_audit(AuditEvent(
        event_type="availability_changed",
        model_id=model_id,
        result="success",
        details=f"is_available={body.is_available}",
    ))

    return model


# ---------------------------------------------------------------------------
# Routes — Health
# ---------------------------------------------------------------------------

@app.get("/api/v1/models/health", response_model=list[ModelHealth])
async def list_health(x_roles: str = Header(default="", alias="x-roles")):
    """Health status for all models."""
    _check_roles(x_roles, _READ_ROLES)
    return _registry.get_all_health()


@app.get("/api/v1/models/{model_id}/health", response_model=ModelHealth)
async def get_model_health(
    model_id: str,
    x_roles: str = Header(default="", alias="x-roles"),
):
    """Health status for a single model."""
    _check_roles(x_roles, _READ_ROLES)
    health = _registry.get_health(model_id)
    if health is None:
        raise HTTPException(status_code=404, detail="FILE_NOT_FOUND")
    return health


# ---------------------------------------------------------------------------
# Routes — Audit
# ---------------------------------------------------------------------------

@app.get("/api/v1/audit")
async def list_audit_events(
    model_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    x_roles: str = Header(default="", alias="x-roles"),
):
    """List recent audit events."""
    _check_roles(x_roles, _READ_ROLES)

    if _repo is None:
        return []

    return await _repo.get_audit_events(model_id=model_id, limit=limit)


# ---------------------------------------------------------------------------
# Liveness / Readiness probes
# ---------------------------------------------------------------------------

@app.get("/healthz")
async def healthz():
    """Liveness probe — is the process alive?"""
    return {"status": "ok"}


@app.get("/readyz")
async def readyz():
    """Readiness probe — is the service ready to serve traffic?

    Checks:
    - Registry is loaded (has models or registry path was configured)
    - Database connection (if configured)
    """
    checks = {
        "registry": "ok" if _config.model_registry_path or _registry.list_all() else "no_models",
        "database": "ok" if _db_pool is not None else "not_configured",
    }

    # Quick DB ping if pool exists
    if _db_pool is not None:
        try:
            async with _db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            checks["database"] = "ok"
        except Exception as exc:
            checks["database"] = f"error: {exc}"

    all_ok = all(v == "ok" for v in checks.values())
    return {"status": "ok" if all_ok else "degraded", "checks": checks}


# ---------------------------------------------------------------------------
# Report inference result (called by inference-gateway after a call completes)
# ---------------------------------------------------------------------------

class InferenceResultRequest(BaseModel):
    model_id: str
    success: bool
    error_code: Optional[str] = None


@app.post("/api/v1/models/report-result", status_code=204)
async def report_inference_result(
    body: InferenceResultRequest,
    x_roles: str = Header(default="", alias="x-roles"),
):
    """Report whether an inference call succeeded or failed.

    Called by the inference-gateway after completing a call. Updates the
    circuit breaker for the model.
    """
    # Internal service call — requires Operator or higher
    _check_roles(x_roles, _READ_ROLES)

    if body.success:
        _model_router.report_success(body.model_id)
    else:
        _model_router.report_failure(body.model_id)

    await _emit_audit(AuditEvent(
        event_type="inference_result",
        model_id=body.model_id,
        result="success" if body.success else "error",
        error_code=body.error_code,
    ))
