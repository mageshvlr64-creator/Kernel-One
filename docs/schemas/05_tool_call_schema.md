# Tool Call Schema

> Directory: `docs/schemas/` · File: `05_tool_call_schema.md` · Kind: **schema**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `04_execution_schema.md` · Next: `06_model_schema.md`

## Purpose

**Tool Call Schema** documents the exact on-disk/on-wire field list, types, and constraints for "tool call schema" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Tool Call Schema is a named schema within the `schemas/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Tool Call Schema at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Tool Call Schema require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Tool Call Schema is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Tool Call Schema enforces the same rule set described here — a feature that reads
   Tool Call Schema differently than documented here is a bug in that feature, not a variant.
3. Where Tool Call Schema interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Tool Call Schema interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/domain/01_domain_model.md`
- `docs/api/01_api_overview.md`

## Acceptance criteria

- [ ] Tool Call Schema behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Tool Call Schema contradicts a related document listed above.
- [ ] Tool Call Schema is covered by at least one test referenced from `docs/testing/`.
- [ ] Tool Call Schema requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Tool Call Schema, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Tool Call Schema that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Tool Call Schema are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
