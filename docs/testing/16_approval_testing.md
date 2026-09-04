# Approval Testing

> Covers `features/16_human_approval/` — the state machine and bypass resistance.

## Required tests

- `TEST-APPROVAL-001`: a high-risk step blocks execution until `decision=approved` exists.
- `TEST-APPROVAL-002` (referenced from `security/15_approval_bypass.md`): editing the gated
  action after `REQUESTED` invalidates the approval (re-approval rule) — attempting to execute
  against the stale approval fails.
- Expiry: an approval past `APPROVAL_EXPIRY_HOURS` transitions to `EXPIRED` and the gated
  action fails, rather than remaining executable indefinitely.
