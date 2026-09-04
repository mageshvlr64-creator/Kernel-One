# Startup

> Operational runbook. Concrete, ordered steps — not a description of what the feature does
> (see the relevant `docs/features/` file for that).

## Procedure

1. Verify `NETWORK_MODE` is set correctly for this deployment before starting any container (`16_ENVIRONMENT_AND_CONFIGURATION.md`).
2. Start Database and Object Storage first; wait for their health checks to pass (`deployment/13_health_checks.md`).
3. Run pending migrations (`schemas/01_database_schema.md` migration policy).
4. Start Identity Service, Policy Engine, Audit Service (build order phase 1).
5. Start Model Management + Inference Gateway; wait for at least one model's health check to pass.
6. Start remaining services per `09_BUILD_ORDER.md` phase order.
7. Verify `/readyz` returns 200 before routing any user traffic.

## Related

- `docs/deployment/13_health_checks.md`
- `docs/09_BUILD_ORDER.md`
- `docs/operations/01_operator_guide.md`
