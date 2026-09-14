# Model Router Service

Routes inference requests to the appropriate model/provider with fallback and circuit-breaking.

## Ownership
**Character 1 — Foundation & Inference** (see `TEAM.md`)

## What this service does
- Maintains the model registry (which models exist, their capabilities, classification ceilings)
- Selects the best model for a given request (capabilities, classification, provider preference, size constraints)
- Tracks per-model health via background polling of provider endpoints
- Implements per-model circuit breakers (open after 5 failures in 60s, half-open probe every 15s per `runtime/11_retry_policy.md`)
- Emits audit events on every selection request (success or failure)

## Endpoints
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/models` | List all registered models |
| `GET` | `/api/v1/models/{id}` | Get a single model |
| `POST` | `/api/v1/models` | Register/update a model (Admin only) |
| `DELETE` | `/api/v1/models/{id}` | Unregister a model (Admin only) |
| `POST` | `/api/v1/models/select` | Select the best model for a request |
| `PATCH` | `/api/v1/models/{id}/availability` | Toggle model availability (Admin only) |
| `GET` | `/api/v1/models/health` | Health status for all models |
| `GET` | `/api/v1/models/{id}/health` | Health status for one model |
| `POST` | `/api/v1/models/report-result` | Report inference success/failure (updates circuit breaker) |
| `GET` | `/api/v1/audit` | Recent audit events |
| `GET` | `/healthz` | Liveness probe |
| `GET` | `/readyz` | Readiness probe |

## Configuration
All config via environment variables (see `docs/16_ENVIRONMENT_AND_CONFIGURATION.md`):
- `MODEL_REGISTRY_PATH` — path to model registry JSON (required)
- `DATABASE_URL` — PostgreSQL connection string (optional; enables persistence)
- `VLLM_BASE_URL`, `OLLAMA_BASE_URL`, `LLAMACPP_BASE_URL` — provider endpoints
- `HEALTH_POLL_INTERVAL_SECONDS` — how often to check provider health (default: 30)
- `CIRCUIT_BREAKER_FAILURE_THRESHOLD` — failures before open (default: 5)
- `CIRCUIT_BREAKER_WINDOW_SECONDS` — failure counting window (default: 60)

## Running locally
```bash
export MODEL_REGISTRY_PATH=./models.json
export DATABASE_URL=postgresql://user:pass@localhost:5432/model_router
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

## Running tests
```bash
pytest tests/ -v
```

## Docker
```bash
docker build -f infra/docker/model-router.Dockerfile -t model-router .
```
