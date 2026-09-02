# Error Codes

> Directory: `docs/reference/` · File: `01_error_codes.md` · Kind: **reference table**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: _(first document in this directory)_ · Next: `02_status_codes.md`

## Purpose

**Error Codes** documents a lookup table other documents point to for "error codes" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Error Codes is a named reference table within the `reference/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Error Codes at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Error Codes require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Error Codes is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Error Codes enforces the same rule set described here — a feature that reads
   Error Codes differently than documented here is a bug in that feature, not a variant.
3. Where Error Codes interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Error Codes interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/18_DOCUMENTATION_INDEX.md`

## Acceptance criteria

- [ ] Error Codes behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Error Codes contradicts a related document listed above.
- [ ] Error Codes is covered by at least one test referenced from `docs/testing/`.
- [ ] Error Codes requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Error Codes, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Error Codes that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Error Codes are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
