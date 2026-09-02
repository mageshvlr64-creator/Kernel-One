# Path Traversal

> Directory: `docs/security/` · File: `09_path_traversal.md` · Kind: **threat**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `08_sandbox_escape.md` · Next: `10_privilege_escalation.md`

## Purpose

**Path Traversal** documents a specific threat, where it can occur, and its mitigation for "path traversal" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Path Traversal is a named threat within the `security/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Path Traversal at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Path Traversal require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Path Traversal is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Path Traversal enforces the same rule set described here — a feature that reads
   Path Traversal differently than documented here is a bug in that feature, not a variant.
3. Where Path Traversal interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Path Traversal interacts with risk or exposure, treat it as **high**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/security/01_security_architecture.md`
- `docs/features/19_identity_and_rbac.md`

## Acceptance criteria

- [ ] Path Traversal behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Path Traversal contradicts a related document listed above.
- [ ] Path Traversal is covered by at least one test referenced from `docs/testing/`.
- [ ] Path Traversal requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Path Traversal, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Path Traversal that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Path Traversal are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
