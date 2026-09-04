# Incident Response

> Operational runbook. Concrete, ordered steps — not a description of what the feature does
> (see the relevant `docs/features/` file for that).

## Procedure

1. Identify scope using `correlation_id` from the affected user's error message, cross-referenced in `api/19_audit_api.md`.
2. Classify severity: data exposure beyond a user's clearance is always Sev1 (see `security/`); a single failed Task is Sev3 or lower.
3. For Sev1/Sev2: follow `11_security_incidents.md`; for network violations specifically, follow `12_network_incidents.md`.
4. Document root cause and remediation as a `20_DECISION_LOG.md` entry if it reveals a design gap, not just a bug fix.

## Related

- `docs/deployment/13_health_checks.md`
- `docs/09_BUILD_ORDER.md`
- `docs/operations/01_operator_guide.md`
