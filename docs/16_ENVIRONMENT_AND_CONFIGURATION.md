# Environment and Configuration (Canonical)

> Single owner for every configuration key. No feature document defines its own config key
> without adding it here in the same change.

## Format

`.env` file (local dev) or environment variables (containers), loaded once at process start,
validated against a schema (`schemas/19_configuration_schema.md`) — invalid/missing required
values fail startup immediately, never fall back to a silent default for security-relevant keys.

## Core keys

| Key | Required | Default | Secret? | Notes |
|---|---|---|---|---|
| `NETWORK_MODE` | yes | `air_gapped` | no | `air_gapped` \| `restricted` \| `on_premise` — REQ-NET-002 |
| `DATABASE_URL` | yes | — | yes | PostgreSQL connection string |
| `OBJECT_STORAGE_ENDPOINT` | yes | — | no | MinIO/S3-compatible endpoint |
| `OBJECT_STORAGE_ACCESS_KEY` | yes | — | yes | — |
| `OBJECT_STORAGE_SECRET_KEY` | yes | — | yes | — |
| `JWT_SIGNING_KEY` | yes | — | yes | Generated at first deploy, never hardcoded; rotation procedure in `operations/06_model_operations.md`-adjacent ops runbook |
| `AGENT_MAX_STEPS` | no | `20` | no | REQ-FUNC-002, CONFIG DEFAULT |
| `AGENT_MAX_REPLANS` | no | `3` | no | CONFIG DEFAULT |
| `APPROVAL_EXPIRY_HOURS` | no | `24` | no | CONFIG DEFAULT |
| `MAX_UPLOAD_SIZE_BYTES` | no | `209715200` (200MB) | no | CONFIG DEFAULT |
| `MODEL_REGISTRY_PATH` | yes | — | no | Path/URI to the model registry config (`features/01_model_management/`) |
| `RESTRICTED_MODE_ALLOWLIST` | only if `NETWORK_MODE=restricted` | — | no | Comma-separated host:port allowlist, REQ-NET-002 |
| `RATE_LIMIT_PER_MINUTE` | no | `60` | no | `schemas/02_api_schema.md` |
| `LOG_LEVEL` | no | `info` | no | `debug` \| `info` \| `warn` \| `error` |
| `OTEL_EXPORTER_ENDPOINT` | no | `http://localhost:4317` (internal only) | no | must resolve to a `localhost`/internal address; never external |

## Precedence

1. Environment variable (highest)
2. `.env` file (local development only — never used in `on_premise`/`restricted`/`air_gapped`
   production images)
3. Schema-declared default (only for keys marked "no" under Required)

## Per-environment profiles

- **Development:** `.env.development` — `NETWORK_MODE=restricted` permitted for pulling
  dependencies during setup only; must be switched to `air_gapped` before any sovereignty test.
- **Production (air-gapped):** `NETWORK_MODE=air_gapped`, no `.env` file baked into the image;
  all secrets injected via the container orchestrator's secret mechanism, never a file in the
  image layer.

## Rule

Configuration definitions never live inside a `features/` document — a feature document may
reference a key by name (e.g. "see `AGENT_MAX_STEPS` in `16_ENVIRONMENT_AND_CONFIGURATION.md`")
but does not restate its default or type.
