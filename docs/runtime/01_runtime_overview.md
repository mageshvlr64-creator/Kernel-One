# Runtime Overview

> Directory: `docs/runtime/` · File: `01_runtime_overview.md` · Kind: **runtime rule**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: _(first document in this directory)_ · Next: `02_task_lifecycle.md`

## Purpose

**Runtime Overview** documents lifecycle, state-machine, or concurrency behavior for "runtime overview" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Runtime Overview is a named runtime rule within the `runtime/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Runtime Overview at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Runtime Overview require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Runtime Overview is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Runtime Overview enforces the same rule set described here — a feature that reads
   Runtime Overview differently than documented here is a bug in that feature, not a variant.
3. Where Runtime Overview interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Runtime Overview interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/04_SYSTEM_ARCHITECTURE.md`
- `docs/failures/01_failure_handling_philosophy.md`

## Acceptance criteria

- [ ] Runtime Overview behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Runtime Overview contradicts a related document listed above.
- [ ] Runtime Overview is covered by at least one test referenced from `docs/testing/`.
- [ ] Runtime Overview requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Runtime Overview, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Runtime Overview that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Runtime Overview are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
