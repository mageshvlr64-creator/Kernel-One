# Approval Workflow

> End-to-end workflow specification. References the specific features involved rather than
> restating their internal behavior.

## Requirements implemented

REQ-FUNC-003

## Steps

1. A plan step or artifact export is classified risk=high (reference/03_risk_levels.md)
2. Task transitions to WAITING_APPROVAL; Approval row created (state=REQUESTED)
3. Administrator/SecurityOfficer reviews via ui/11_approval_ui.md and decides
4. On approve: Task resumes EXECUTING. On reject: Task transitions to FAILED with reason. On expiry (24h, CONFIG DEFAULT): Approval → EXPIRED, Task → FAILED

## Notes

Canonical state machine: runtime/_state_machines_canonical.md#approval.
