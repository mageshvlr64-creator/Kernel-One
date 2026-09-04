# Health Checks

> The concrete implementation behind `api/24_health_api.md`'s `/healthz`/`/readyz` contract,
> referenced by `operations/02_startup.md`, `04_health_monitoring.md`, and every deployment
> file above.

## Liveness (`/healthz`)

Returns 200 if the process itself is running and its event loop is responsive — does NOT
check downstream dependencies. A liveness failure means "restart this specific process,"
nothing more. Checked every 10s; 3 consecutive failures triggers a container restart.

## Readiness (`/readyz`)

Returns 200 only if every hard dependency listed in `10_DEPENDENCY_GRAPH.md` for that service
is reachable and responding within its own health-check timeout:

| Dependency | Check | Timeout |
|---|---|---|
| Database | `SELECT 1` | 2s |
| Object Storage | `HEAD` on a known bucket | 2s |
| Configured Model(s) | Provider-specific lightweight ping (e.g. vLLM's `/health`) | 5s |
| Policy Engine (for services that depend on it) | In-process call, no network hop in V1 | N/A |

A readiness failure removes the instance from load-balancing (or, in V1 single-node, surfaces
as a degraded state on the Admin Console health dashboard, `ui/16_admin_console_ui.md`) without
restarting the process — the distinction from liveness matters because a database outage
should not trigger endless container restarts of every dependent service.

## Per-service health composition

Each service's `/readyz` only checks *its own* direct dependencies (per `10_DEPENDENCY_GRAPH.md`),
not the full transitive graph — the Admin Console's dashboard composes all services' individual
readiness into one overall system-health view, rather than each service redundantly checking
everything.
