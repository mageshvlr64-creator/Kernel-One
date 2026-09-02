# Model Panel

> Directory: `docs/ui/` · File: `14_model_panel.md` · Kind: **UI surface**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `13_network_panel.md` · Next: `15_knowledge_browser.md`

## Purpose

**Model Panel** documents layout, states, and interaction rules for one screen or panel for "model panel" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Model Panel is a named UI surface within the `ui/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Model Panel at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Model Panel require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Model Panel is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Model Panel enforces the same rule set described here — a feature that reads
   Model Panel differently than documented here is a bug in that feature, not a variant.
3. Where Model Panel interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Model Panel interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/05_ARCHITECTURAL_PRINCIPLES.md`
- `docs/ui/01_ui_architecture.md`

## Acceptance criteria

- [ ] Model Panel behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Model Panel contradicts a related document listed above.
- [ ] Model Panel is covered by at least one test referenced from `docs/testing/`.
- [ ] Model Panel requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Model Panel, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Model Panel that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Model Panel are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
