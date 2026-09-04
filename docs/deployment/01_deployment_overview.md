# Deployment Overview

> Index for the deployment directory. Each profile/mode combination below is a concrete,
> named target — not an abstract capability.

## Deployment matrix

| Profile | Network mode | File |
|---|---|---|
| PROFILE-A (dev) | `restricted` (setup only) → `air_gapped` for testing | `02_local_development.md` |
| PROFILE-B (demo) | `air_gapped` | `06_cpu_only_demo.md` (fallback), primary path via `03_docker_compose.md` |
| PROFILE-C/D (production) | `air_gapped` / `restricted` / `on_premise` per `07_air_gapped_deployment.md`, `08_restricted_network_deployment.md`, `09_on_premise_deployment.md` |

## Common prerequisites (all profiles)

- Docker Engine + Docker Compose (or the orchestrator chosen for PROFILE-C/D).
- Model weights pre-downloaded to the host per `07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`'s
  reference registry (checksum-verified, `security/22_supply_chain_security.md`).
- `.env` populated per `16_ENVIRONMENT_AND_CONFIGURATION.md` (never committed to version
  control).

## First deployment checklist

1. `02_local_development.md` or the target profile's specific file.
2. `13_health_checks.md` — confirm `/readyz` returns 200.
3. Run one demo scenario (`demo/01_demo_overview.md`) as a smoke test before considering the
   deployment live.
