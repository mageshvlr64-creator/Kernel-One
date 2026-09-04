# Docker Compose Deployment

> The primary V1 deployment mechanism for PROFILE-B/C single-node.

## Compose file structure

`infra/compose/docker-compose.yml` defines one service per entry in
`15_CODEBASE_TARGET_STRUCTURE.md`'s `services/` directory, plus `postgres` (with the pgvector
extension baked into the image) and `minio`. Each service:

- Has explicit `cpus`/`mem_limit` resource constraints matching its expected load
  (`performance/` budgets).
- Joins a single internal bridge network (`sovereign-net`) with no external route except the
  reverse-proxy container's port binding.
- The `code-execution-sandbox` service (or the ephemeral containers it spawns per task) is
  additionally configured with `network_mode: none`.

## Bringing it up

```
docker compose -f infra/compose/docker-compose.yml up -d
```

Followed by `operations/02_startup.md`'s ordered health-check verification.

## Configuration

All `16_ENVIRONMENT_AND_CONFIGURATION.md` keys are injected via Compose's `env_file` directive
pointing at the deployment's `.env` (never baked into the image).
