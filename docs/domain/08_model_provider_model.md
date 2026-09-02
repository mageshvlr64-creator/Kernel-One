# Model Provider Model

> Directory: `docs/domain/` · File: `08_model_provider_model.md` · Kind: **domain entity**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `07_knowledge_model.md` · Next: `09_agent_model.md`

## Purpose

**Model Provider Model** documents a core entity's identity, fields, lifecycle, and relationships for "model provider model" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Model Provider Model is a named domain entity within the `domain/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Model Provider Model at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Model Provider Model require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Model Provider Model is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Model Provider Model enforces the same rule set described here — a feature that reads
   Model Provider Model differently than documented here is a bug in that feature, not a variant.
3. Where Model Provider Model interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Model Provider Model interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/04_SYSTEM_ARCHITECTURE.md`
- `docs/schemas/01_database_schema.md`

## Acceptance criteria

- [ ] Model Provider Model behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Model Provider Model contradicts a related document listed above.
- [ ] Model Provider Model is covered by at least one test referenced from `docs/testing/`.
- [ ] Model Provider Model requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Model Provider Model, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Model Provider Model that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Model Provider Model are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
