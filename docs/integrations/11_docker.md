# Docker Integration

> The container runtime backing both service deployment (`deployment/03_docker_compose.md`)
> and the Code Execution sandbox (`features/09_code_execution/`) — these are two distinct uses
> of the same underlying technology, worth distinguishing.

## Service deployment use

Standard Compose-orchestrated long-running service containers, resource-limited per
`performance/03_memory_budgets.md`/`04_cpu_budgets.md`.

## Sandbox use

Ephemeral, per-task containers created and destroyed by the Code Execution feature
(`features/09_code_execution/04_container_creation.md`, `11_container_cleanup.md`), with the
stricter isolation profile in DEC-005 (`--network=none`, non-root, minimal capabilities,
hard resource limits) — this use case has a materially different security posture than the
first and must not be confused with it when reviewing container security
(`security/21_container_security.md`).

## Health check

Docker daemon reachability, per `failures/35_container_failures.md`.
