# Approval Bypass

> Threat entry. Format follows `01_security_architecture.md`'s convention: threat description,
> where it can occur, mitigation, and traceability to requirements/tests.

## Threat

An attempt to execute a high-risk action without a valid, approved Approval record — e.g. by re-submitting the same action with a different ID, or racing the approval-expiry check.

## Where it can occur

Human Approval (features/16_human_approval/), Tool Gateway.

## Mitigation

The gated action's execution path checks for an `Approval` row with `decision=approved` at execution time (not just plan-generation time), and editing the gated action after `REQUESTED` invalidates the approval (re-approval rule, runtime/_state_machines_canonical.md#approval).

## Traceability

- Requirements: `REQ-FUNC-003`
- Tests: `TEST-APPROVAL-002 (add to testing/16_approval_testing.md if not already present)`

## Residual risk

Every mitigation above reduces but does not claim to eliminate risk to zero — where a
mitigation is preventive (e.g. container isolation), a detective control (audit logging) is
also in place so a successful bypass is still discoverable after the fact, per
`security/01_security_architecture.md`'s defense-in-depth principle.
