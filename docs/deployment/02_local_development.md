# Local Development

> PROFILE-A setup, for engineers/agents building against this specification.

## Steps

1. Clone the repository (`15_CODEBASE_TARGET_STRUCTURE.md`).
2. Copy `.env.example` to `.env.development`; set `NETWORK_MODE=restricted` temporarily to
   allow pulling base images and packages (switch to `air_gapped` before any sovereignty-
   related testing).
3. `docker compose -f infra/compose/docker-compose.dev.yml up -d` — starts Database, Object
   Storage, and a single lightweight model (the `cpu-fallback` capability slot,
   `07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`) for fast local iteration without requiring a
   GPU.
4. Run migrations (`schemas/01_database_schema.md`).
5. Seed a development Administrator user and a Restricted User (matching DEC-006's two
   demo-rehearsed roles) via the seed script.
6. `GET /readyz` should return 200 once all dependencies are healthy.

## Development-only allowances

`.env.development` may set `NETWORK_MODE=restricted` — this is the **one** environment where
that's acceptable outside an explicit `restricted`-mode production deployment, and only for
initial setup (pulling dependencies), never left on during actual feature testing.
