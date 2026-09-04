# Disaster Recovery

> The scenario-driven complement to `09_restore_operations.md`'s mechanical steps.

## Scenarios and response

| Scenario | Response |
|---|---|
| Single service crash (e.g. Agent Kernel process dies) | Orchestrator auto-restarts per `04_health_monitoring.md`; in-flight Tasks recover per `runtime/14_resume_and_recovery.md`. No backup/restore needed. |
| Database corruption (detected via failed hash-chain verification, REQ-SEC-005) | Full `09_restore_operations.md` from the most recent backup that passes verification; treat as a Sev1 security incident (`11_security_incidents.md`) until corruption cause is confirmed benign (e.g. disk failure vs. tampering). |
| Object storage volume failure | Restore Documents/Artifacts from the nightly snapshot; database remains authoritative for metadata, so no Task/Evidence/Approval history is lost even if some file *content* must be re-derived (e.g. re-run OCR on a lost original if no backup copy exists). |
| Full host loss (single-node V1 deployment, DEC-001) | Provision a new host matching `07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md` PROFILE-B/C, run `02_startup.md` against restored data. **V1 has no hot standby** — this is an accepted single-node-first tradeoff (DEC-001); recovery time is bounded by restore time (`09_restore_operations.md`), not instantaneous failover. |
| Compromised credentials (e.g. leaked `JWT_SIGNING_KEY`) | Rotate the key immediately (invalidates all active sessions), force re-authentication, audit all activity since the suspected compromise window via `19_audit_api.md`. |

## Recovery time / recovery point objectives

- **RPO (Recovery Point Objective):** ≤ 24 hours (nightly backup) without WAL archiving
  configured; near-zero with WAL archiving enabled — **CONFIG DEFAULT / deployment choice**,
  not benchmarked, operator must explicitly choose based on their own risk tolerance.
- **RTO (Recovery Time Objective):** target under 2 hours for a single-node restore on
  PROFILE-B/C — **DESIGN LIMIT**, not yet drilled/timed against a real restore rehearsal (this
  gap should be closed with an actual DR drill before calling V1 production-ready, tracked
  alongside `20_DECISION_LOG.md` DEC-014's benchmark-validation theme).

## Required drill

At least one full restore-from-backup drill should be performed in a non-production
environment before this deployment is relied upon for real data — this is a recommendation
this document makes explicit rather than assuming implicitly.
