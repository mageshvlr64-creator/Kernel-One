# Network Incident Response

> Operational runbook. Concrete, ordered steps — not a description of what the feature does
> (see the relevant `docs/features/` file for that).

## Procedure

1. Cross-reference the `network_events` table (`schemas/17_network_event_schema.md`) against the incident time window.
2. If an egress attempt succeeded (should be impossible under REQ-NET-001): treat as Sev1, isolate the host, and audit the specific code path that made the call.
3. If an egress attempt was correctly blocked: confirm it was logged and visible on the sovereignty panel (`ui/13_network_panel.md`) — a blocked-but-unlogged attempt is itself a defect (REQ-AUD-001).

## Related

- `docs/deployment/13_health_checks.md`
- `docs/09_BUILD_ORDER.md`
- `docs/operations/01_operator_guide.md`
