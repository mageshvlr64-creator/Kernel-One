# Contract Testing

> Directory: `docs/testing/` · File: `04_contract_testing.md` · Kind: **test approach**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `03_integration_testing.md` · Next: `05_api_testing.md`

## Purpose

**Contract Testing** documents what must be covered and how pass/fail is judged for "contract testing" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Contract Testing is a named test approach within the `testing/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Contract Testing at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Contract Testing require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Contract Testing is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Contract Testing enforces the same rule set described here — a feature that reads
   Contract Testing differently than documented here is a bug in that feature, not a variant.
3. Where Contract Testing interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Contract Testing interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/testing/01_testing_strategy.md`
- `docs/12_GLOBAL_ACCEPTANCE_CRITERIA.md`

## Acceptance criteria

- [ ] Contract Testing behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Contract Testing contradicts a related document listed above.
- [ ] Contract Testing is covered by at least one test referenced from `docs/testing/`.
- [ ] Contract Testing requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Contract Testing, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Contract Testing that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Contract Testing are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
