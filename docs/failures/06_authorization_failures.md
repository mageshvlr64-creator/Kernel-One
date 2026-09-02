# Authorization Failures

> Directory: `docs/failures/` · File: `06_authorization_failures.md` · Kind: **failure mode**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `05_authentication_failures.md` · Next: `07_model_failures.md`

## Purpose

**Authorization Failures** documents a named failure, its detection signal, and system response for "authorization failures" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Authorization Failures is a named failure mode within the `failures/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Authorization Failures at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Authorization Failures require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Authorization Failures is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Authorization Failures enforces the same rule set described here — a feature that reads
   Authorization Failures differently than documented here is a bug in that feature, not a variant.
3. Where Authorization Failures interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Authorization Failures interacts with risk or exposure, treat it as **high**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/failures/01_failure_handling_philosophy.md`
- `docs/runtime/11_retry_policy.md`

## Acceptance criteria

- [ ] Authorization Failures behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Authorization Failures contradicts a related document listed above.
- [ ] Authorization Failures is covered by at least one test referenced from `docs/testing/`.
- [ ] Authorization Failures requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Authorization Failures, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Authorization Failures that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Authorization Failures are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
