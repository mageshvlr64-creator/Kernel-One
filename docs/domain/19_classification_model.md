# Classification Model

> Directory: `docs/domain/` · File: `19_classification_model.md` · Kind: **domain entity**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `18_memory_model.md` · Next: _(last document in this directory)_

## Purpose

**Classification Model** documents a core entity's identity, fields, lifecycle, and relationships for "classification model" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Classification Model is a named domain entity within the `domain/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Classification Model at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Classification Model require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Classification Model is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Classification Model enforces the same rule set described here — a feature that reads
   Classification Model differently than documented here is a bug in that feature, not a variant.
3. Where Classification Model interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Classification Model interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/04_SYSTEM_ARCHITECTURE.md`
- `docs/schemas/01_database_schema.md`

## Acceptance criteria

- [ ] Classification Model behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Classification Model contradicts a related document listed above.
- [ ] Classification Model is covered by at least one test referenced from `docs/testing/`.
- [ ] Classification Model requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Classification Model, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Classification Model that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Classification Model are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
