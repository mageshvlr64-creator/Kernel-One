# Policy Denied Workflow

> Directory: `docs/workflows/` · File: `10_policy_denied_workflow.md` · Kind: **end-to-end workflow**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `09_approval_workflow.md` · Next: `11_model_failure_workflow.md`

## Purpose

**Policy Denied Workflow** documents a full user scenario crossing multiple features for "policy denied workflow" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Policy Denied Workflow is a named end-to-end workflow within the `workflows/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Policy Denied Workflow at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Policy Denied Workflow require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Policy Denied Workflow is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Policy Denied Workflow enforces the same rule set described here — a feature that reads
   Policy Denied Workflow differently than documented here is a bug in that feature, not a variant.
3. Where Policy Denied Workflow interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Policy Denied Workflow interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/demo/01_demo_overview.md`

## Acceptance criteria

- [ ] Policy Denied Workflow behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Policy Denied Workflow contradicts a related document listed above.
- [ ] Policy Denied Workflow is covered by at least one test referenced from `docs/testing/`.
- [ ] Policy Denied Workflow requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Policy Denied Workflow, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Policy Denied Workflow that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Policy Denied Workflow are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
