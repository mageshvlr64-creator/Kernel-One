# Libreoffice

> Directory: `docs/integrations/` · File: `10_libreoffice.md` · Kind: **integration**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `09_pymupdf.md` · Next: `11_docker.md`

## Purpose

**Libreoffice** documents the contract with a specific third-party component for "libreoffice" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Libreoffice is a named integration within the `integrations/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Libreoffice at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Libreoffice require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Libreoffice is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Libreoffice enforces the same rule set described here — a feature that reads
   Libreoffice differently than documented here is a bug in that feature, not a variant.
3. Where Libreoffice interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Libreoffice interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/integrations/01_integration_architecture.md`
- `docs/06_TECHNOLOGY_STACK.md`

## Acceptance criteria

- [ ] Libreoffice behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Libreoffice contradicts a related document listed above.
- [ ] Libreoffice is covered by at least one test referenced from `docs/testing/`.
- [ ] Libreoffice requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Libreoffice, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Libreoffice that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Libreoffice are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
