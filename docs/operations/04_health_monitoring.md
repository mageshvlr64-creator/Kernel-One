# Health Monitoring

> Operational runbook. Concrete, ordered steps — not a description of what the feature does
> (see the relevant `docs/features/` file for that).

## Procedure

1. `/healthz` (liveness) checked every 10s by the orchestrator; 3 consecutive failures triggers a restart.
2. `/readyz` (readiness) checked every 5s; failure removes the instance from load balancing without restarting it.
3. Dashboard (`features/25_observability/`) surfaces per-dependency health: Database, Object Storage, each configured Model, Vector index.
4. Alert thresholds: any dependency unhealthy for > 60s pages the on-call operator (`11_alerting.md`).

## Related

- `docs/deployment/13_health_checks.md`
- `docs/09_BUILD_ORDER.md`
- `docs/operations/01_operator_guide.md`
