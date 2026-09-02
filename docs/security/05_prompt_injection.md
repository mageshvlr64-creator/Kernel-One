# Prompt Injection

> Directory: `docs/security/` · File: `05_prompt_injection.md` · Kind: **threat**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `04_attack_surface.md` · Next: `06_data_exfiltration.md`

## Purpose

**Prompt Injection** documents a specific threat, where it can occur, and its mitigation for "prompt injection" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Prompt Injection is a named threat within the `security/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Prompt Injection at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Prompt Injection require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Prompt Injection is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Prompt Injection enforces the same rule set described here — a feature that reads
   Prompt Injection differently than documented here is a bug in that feature, not a variant.
3. Where Prompt Injection interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Prompt Injection interacts with risk or exposure, treat it as **high**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/security/01_security_architecture.md`
- `docs/features/19_identity_and_rbac.md`

## Acceptance criteria

- [ ] Prompt Injection behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Prompt Injection contradicts a related document listed above.
- [ ] Prompt Injection is covered by at least one test referenced from `docs/testing/`.
- [ ] Prompt Injection requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Prompt Injection, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Prompt Injection that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Prompt Injection are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
