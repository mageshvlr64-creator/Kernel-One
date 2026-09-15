# Inference Gateway

Provider-agnostic inference service for the Sovereign AI Workbench (SIH26117).

Normalizes **vLLM** (primary GPU runtime), **Ollama** (secondary), and
**llama.cpp** (CPU fallback) behind a single HTTP contract. Model selection,
availability, and circuit breaking stay with the **model-router** — this
service only executes inference and reports outcomes back.

Character 1 (Foundation & Inference) owns this service — see `TEAM.md`.

## Endpoints

| Method | Path                      | Description                                          |
|--------|---------------------------|------------------------------------------------------|
| POST   | `/api/v1/infer`           | Provider-agnostic chat inference                      |
| GET    | `/api/v1/providers/health`| Aggregated provider health (best-effort)              |
| GET    | `/healthz`                | Liveness probe                                        |
| GET    | `/readyz`                 | Readiness probe (router + adapters required, DB optional) |

### POST /api/v1/infer

```json
{
  "messages": [{"role": "user", "content": "Summarize this P&ID drawing"}],
  "kind": "text",
  "selection": {"required_capabilities": ["coding"], "max_classification": "CONFIDENTIAL"}
}
```

- Pass `model_id` to pin a model, **or** `selection` criteria to let the
  model-router choose (exactly one of the two).
- Response is normalized across providers: `content`, `model_id`,
  `provider`, `finish_reason`, `usage`, `latency_ms`, `fallback_used`.

Errors use the canonical registry (`docs/reference/01_error_codes.md`):
`MODEL_UNAVAILABLE`, `MODEL_RESOURCE_EXHAUSTED`, `INFERENCE_TIMEOUT`,
`POLICY_DENIED`.

## How it works

1. **Resolve** — explicit `model_id`, or ask the model-router
   `POST /api/v1/models/select` for `(model, fallback_chain)`.
2. **Execute** — provider adapter call wrapped in the runtime timeout
   budget (30s text / 60s vision per `runtime/11_retry_policy.md`).
3. **Retry / fallback** — one retry on `MODEL_UNAVAILABLE` /
   `INFERENCE_TIMEOUT` with fixed 500ms backoff, then walk the router's
   fallback chain.
4. **Report** — every attempt reports success/failure to the router's
   `POST /api/v1/models/report-result` (feeds its circuit breakers).
5. **Audit** — every call persists an event to `inference_audit_events`
   (if `DATABASE_URL` is set).

## Configuration (environment variables)

| Variable                        | Default                 | Purpose                            |
|---------------------------------|-------------------------|------------------------------------|
| `MODEL_ROUTER_URL`              | `http://localhost:8002` | Model-router base URL              |
| `MODEL_ROUTER_TIMEOUT_SECONDS`  | `5`                     | Router call timeout                |
| `VLLM_BASE_URL`                 | `http://localhost:8000` | vLLM server                        |
| `OLLAMA_BASE_URL`               | `http://localhost:11434`| Ollama server                      |
| `LLAMACPP_BASE_URL`             | `http://localhost:8080` | llama-server                       |
| `INFERENCE_TIMEOUT_TEXT_SECONDS`| `30`                    | Text timeout budget                |
| `INFERENCE_TIMEOUT_VISION_SECONDS` | `60`                 | Vision timeout budget              |
| `INFERENCE_MAX_RETRIES`         | `1`                     | Retries per candidate              |
| `INFERENCE_RETRY_BACKOFF_SECONDS` | `0.5`                 | Fixed backoff between retries      |
| `INFERENCE_ENABLE_FALLBACK`     | `true`                  | Walk fallback chain on failure     |
| `DATABASE_URL`                  | *(unset)*               | PostgreSQL for audit events        |
| `LOG_LEVEL`                     | `info`                  | Logging verbosity                  |

## Running

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8003
```

Docker: see `infra/docker/inference-gateway.Dockerfile`.

## Tests

```bash
pytest tests/
```

No real providers or router needed — HTTP interactions are faked with
respx-style stubs over `httpx.MockTransport` and monkeypatched clients.

## Known limitations

- Trusts `x-roles` forwarded by the platform gateway; real JWT validation
  is Character 5's identity-service.
- Provider resolution for unprefixed model IDs defaults to vLLM (DEC-004);
  refine when the router exposes a model→provider lookup endpoint.
