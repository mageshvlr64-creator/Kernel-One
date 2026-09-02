# Attack Surface

> Directory: `docs/security/` · File: `04_attack_surface.md` · Kind: **threat**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `03_trust_model.md` · Next: `05_prompt_injection.md`

## Purpose

**Attack Surface** documents a specific threat, where it can occur, and its mitigation for "attack surface" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Attack Surface is a named threat within the `security/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Attack Surface at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Attack Surface require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Attack Surface is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Attack Surface enforces the same rule set described here — a feature that reads
   Attack Surface differently than documented here is a bug in that feature, not a variant.
3. Where Attack Surface interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Attack Surface interacts with risk or exposure, treat it as **high**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/security/01_security_architecture.md`
- `docs/features/19_identity_and_rbac.md`

## Acceptance criteria

- [ ] Attack Surface behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Attack Surface contradicts a related document listed above.
- [ ] Attack Surface is covered by at least one test referenced from `docs/testing/`.
- [ ] Attack Surface requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Attack Surface, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Attack Surface that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Attack Surface are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
