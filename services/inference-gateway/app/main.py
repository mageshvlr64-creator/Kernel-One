"""Inference Gateway — FastAPI application.

Routes:
  POST /api/v1/infer              — provider-agnostic inference
  GET  /api/v1/providers/health   — aggregated provider health
  GET  /healthz                   — liveness probe
  GET  /readyz                    — readiness probe

Permission model (fails closed, developer rule 11): the gateway trusts
the `x-roles` header forwarded by the platform gateway for now — real
JWT validation is Character 5's identity-service (same stance the
model-router documented in CHANGELOG).
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

import asyncpg
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from .adapters import ADAPTERS, LlamaCppAdapter, OllamaAdapter, VllmAdapter
from .config import GatewayConfig
from .database import InferenceAuditRepository
from .gateway import GatewayValidationError, InferenceGateway
from .router_client import RouterClient
from .schemas import InferenceRequest, InferenceResponse

logger = logging.getLogger("inference-gateway")

# ---------------------------------------------------------------------------
# Shared state — initialized at import (matches the model-router's pattern,
# so TestClient works without running lifespan). DB setup happens in lifespan.
# ---------------------------------------------------------------------------
_config = GatewayConfig()

ADAPTERS["vllm"] = VllmAdapter(
    _config.vllm_base_url, _config.inference_timeout_text_seconds
)
ADAPTERS["ollama"] = OllamaAdapter(
    _config.ollama_base_url, _config.inference_timeout_text_seconds
)
ADAPTERS["llamacpp"] = LlamaCppAdapter(
    _config.llamacpp_base_url, _config.inference_timeout_text_seconds
)

_router_client: RouterClient = RouterClient(
    _config.model_router_url, _config.model_router_timeout_seconds
)
_gateway: InferenceGateway = InferenceGateway(_config, _router_client, None)

_db_pool: Optional[asyncpg.Pool] = None  # type: ignore[type-arg]


# ---------------------------------------------------------------------------
# Lifespan — optional audit DB + shutdown cleanup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    global _db_pool, _gateway

    if _config.database_url:
        try:
            _db_pool = await asyncpg.create_pool(
                _config.database_url, min_size=1, max_size=5
            )
            audit_repo = InferenceAuditRepository(_db_pool)
            await audit_repo.init_schema()
            # Rebuild the gateway with audit persistence attached
            _gateway = InferenceGateway(_config, _router_client, audit_repo)
            logger.info("Connected to PostgreSQL for audit persistence")
        except Exception as exc:
            logger.error("Failed to connect to database: %s", exc)
    else:
        logger.warning("DATABASE_URL not set — running without audit persistence")

    yield

    for adapter in ADAPTERS.values():
        await adapter.close()
    ADAPTERS.clear()
    await _router_client.close()
    if _db_pool is not None:
        await _db_pool.close()


app = FastAPI(
    title="Inference Gateway",
    description=(
        "Provider-agnostic inference: normalizes vLLM / Ollama / llama.cpp "
        "behind one contract, routes via the model-router with fallback "
        "(runtime/11_retry_policy.md)"
    ),
    version="0.1.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Permission helper (fail closed)
# ---------------------------------------------------------------------------

_READ_ROLES = {"Operator", "Engineer", "Administrator", "Auditor"}
_INFER_ROLES = {"Operator", "Engineer", "Administrator"}


def _check_roles(x_roles: str, required: set[str]) -> list[str]:
    if not x_roles:
        raise HTTPException(status_code=403, detail="POLICY_DENIED: no roles provided")
    roles = [r.strip() for r in x_roles.split(",") if r.strip()]
    if not any(r in required for r in roles):
        raise HTTPException(
            status_code=403, detail="POLICY_DENIED: insufficient permissions"
        )
    return roles


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[str] = None
    model_id: Optional[str] = None


@app.post(
    "/api/v1/infer",
    response_model=InferenceResponse,
    responses={503: {"model": ErrorResponse}},
)
async def infer(
    request: InferenceRequest,
    x_roles: str = Header(default="", alias="x-roles"),
):
    """Execute a provider-agnostic inference request.

    Either ``model_id`` (explicit) or ``selection`` (router picks) is
    required — exactly one of the two. The response is normalized
    regardless of which provider served it.
    """
    roles = _check_roles(x_roles, _INFER_ROLES)
    actor_id = roles[0]

    try:
        return await _gateway.infer(request, actor_id)
    except GatewayValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        # ProviderError and RouterUnavailableError both surface as 503
        # with the canonical error code envelope (docs/reference/01_error_codes.md).
        error_code = getattr(exc, "error_code", "INTERNAL_ERROR")
        details = getattr(exc, "details", None) or str(exc)
        model_id = getattr(exc, "model_id", None)
        raise HTTPException(
            status_code=503,
            detail={
                "error_code": error_code,
                "message": str(exc),
                "details": details,
                "model_id": model_id,
            },
        ) from exc


@app.get("/api/v1/providers/health")
async def providers_health(
    x_roles: str = Header(default="", alias="x-roles"),
):
    """Aggregated health of all configured providers (best-effort)."""
    _check_roles(x_roles, _READ_ROLES)

    results = []
    for name, adapter in ADAPTERS.items():
        try:
            ok, err = await adapter.health_check()
            results.append({"provider": name, "is_healthy": ok, "error": err})
        except Exception as exc:
            results.append({"provider": name, "is_healthy": False, "error": str(exc)})
    return results


# ---------------------------------------------------------------------------
# Probes
# ---------------------------------------------------------------------------

@app.get("/healthz")
async def healthz():
    """Liveness probe — is the process alive?"""
    return {"status": "ok"}


@app.get("/readyz")
async def readyz():
    """Readiness probe — router client + adapters required, DB optional."""
    checks = {
        "router_client": "ok" if _router_client is not None else "not_initialized",
        "adapters": "ok" if ADAPTERS else "not_initialized",
        "database": "ok" if _db_pool is not None else "not_configured",
    }
    if _db_pool is not None:
        try:
            async with _db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            checks["database"] = "ok"
        except Exception as exc:
            checks["database"] = f"error: {exc}"

    core_ok = checks["router_client"] == "ok" and checks["adapters"] == "ok"
    return {"status": "ok" if core_ok else "degraded", "checks": checks}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8003")),
        log_level=_config.log_level,
    )
