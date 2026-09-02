# Local Speech

> Directory: `docs/later/` · File: `05_local_speech.md` · Kind: **deferred capability**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `04_drawing_intelligence.md` · Next: `06_local_tts.md`

## Purpose

**Local Speech** documents a V2+ idea explicitly out of V1 scope for "local speech" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Local Speech is a named deferred capability within the `later/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Local Speech at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Local Speech require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Local Speech is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Local Speech enforces the same rule set described here — a feature that reads
   Local Speech differently than documented here is a bug in that feature, not a variant.
3. Where Local Speech interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Local Speech interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/02_SCOPE_AND_NON_GOALS.md`

## Acceptance criteria

- [ ] Local Speech behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Local Speech contradicts a related document listed above.
- [ ] Local Speech is covered by at least one test referenced from `docs/testing/`.
- [ ] Local Speech requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Local Speech, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Local Speech that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Local Speech are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
