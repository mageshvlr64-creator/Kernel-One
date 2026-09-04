# Operator Guide (Index)

> Entry point for the human operator running this deployment day-to-day. Each procedure below
> lives in its own file; this file is the map, not a restatement.

## Daily

- Check `04_health_monitoring.md` dashboard — all dependencies green, no sustained alerts.
- Skim `19_audit_api.md`-backed audit viewer (`ui/16_admin_console_ui.md`) for any
  `POLICY_DENIED` or `NETWORK_EGRESS_BLOCKED` events overnight — these are not necessarily
  incidents (denials are the system working correctly) but a spike is worth investigating.

## Weekly

- Verify the most recent backup completed (`08_backup_operations.md`).
- Review `05_log_management.md` disk usage; rotate/archive if approaching the configured
  retention threshold.

## As-needed

- `02_startup.md` / `03_shutdown.md` for planned maintenance windows.
- `06_model_operations.md` when adding, replacing, or retiring a model.
- `10_incident_response.md` → `11_security_incidents.md` / `12_network_incidents.md` for
  anomalies.
- `09_restore_operations.md` / `13_disaster_recovery.md` for data-loss scenarios.

## Escalation

An operator who is not also a Security Officer/Administrator (`reference/05_permission_matrix.md`)
cannot decide Approvals or view the full audit trail — escalate to a role-appropriate person
rather than working around the restriction.
