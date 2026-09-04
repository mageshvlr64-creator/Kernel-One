# Security Incident Response

> Operational runbook. Concrete, ordered steps — not a description of what the feature does
> (see the relevant `docs/features/` file for that).

## Procedure

1. Immediately check `docs/api/19_audit_api.md` filtered by the suspected actor_id and time window.
2. If classification-boundary violation confirmed: identify all documents/artifacts touched, notify affected data owners, revoke the actor's session (`POST /api/v1/auth/logout` equivalent admin action).
3. If a `NETWORK_EGRESS_BLOCKED` audit event correlates with the incident: confirm via `operations/12_network_incidents.md` whether it was blocked successfully or represents a monitoring gap.
4. File a `SEC-TEST-###` case in `testing/21_security_testing.md` if the incident reveals a scenario not already covered.

## Related

- `docs/deployment/13_health_checks.md`
- `docs/09_BUILD_ORDER.md`
- `docs/operations/01_operator_guide.md`
