# Pymupdf

> Directory: `docs/integrations/` · File: `09_pymupdf.md` · Kind: **integration**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `08_paddleocr.md` · Next: `10_libreoffice.md`

## Purpose

**Pymupdf** documents the contract with a specific third-party component for "pymupdf" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Pymupdf is a named integration within the `integrations/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Pymupdf at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Pymupdf require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Pymupdf is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Pymupdf enforces the same rule set described here — a feature that reads
   Pymupdf differently than documented here is a bug in that feature, not a variant.
3. Where Pymupdf interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Pymupdf interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/integrations/01_integration_architecture.md`
- `docs/06_TECHNOLOGY_STACK.md`

## Acceptance criteria

- [ ] Pymupdf behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Pymupdf contradicts a related document listed above.
- [ ] Pymupdf is covered by at least one test referenced from `docs/testing/`.
- [ ] Pymupdf requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Pymupdf, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Pymupdf that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Pymupdf are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
