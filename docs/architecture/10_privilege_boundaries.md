# Privilege Boundaries

> Where privilege level changes, distinct from trust boundaries (`09_trust_boundaries.md`,
> which is about data trust, not privilege).

## Boundaries

- **Restricted User → Analyst** — gains the ability to invoke medium-risk tools
  (`reference/05_permission_matrix.md`).
- **Analyst → SecurityOfficer/Administrator** — gains approval authority over high-risk
  actions and full audit visibility.
- **Administrator → the Policy Engine's own configuration** — even Administrator actions that
  change Policy rows are themselves policy-evaluated and audited (no role, including
  Administrator, has an unaudited path to system state).
- **Application service role → Database superuser** — the application's own DB credentials
  never have `UPDATE`/`DELETE` on `audit_events` (REQ-SEC-005); only a genuinely separate,
  break-glass superuser credential (used only for disaster recovery,
  `operations/13_disaster_recovery.md`) has that privilege, and its use is itself logged
  outside the application's own audit trail (infrastructure-level logging,
  `operations/05_log_management.md`).

## Rule

No privilege boundary above is crossable via a client-supplied field — every crossing requires
either a role stored server-side (`domain/04_user_model.md`) or an explicit administrative
action that is itself audited.
