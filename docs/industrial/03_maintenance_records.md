# Maintenance Records

> Directory: `docs/industrial/` · File: `03_maintenance_records.md` · Kind: **industrial capability**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `02_inspection_reports.md` · Next: `04_sop_compliance.md`

## Purpose

**Maintenance Records** documents a domain-specific capability built on the core platform for "maintenance records" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Maintenance Records is a named industrial capability within the `industrial/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Maintenance Records at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Maintenance Records require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Maintenance Records is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Maintenance Records enforces the same rule set described here — a feature that reads
   Maintenance Records differently than documented here is a bug in that feature, not a variant.
3. Where Maintenance Records interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Maintenance Records interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/industrial/01_industrial_intelligence_overview.md`
- `docs/features/14_evidence_and_provenance.md`

## Acceptance criteria

- [ ] Maintenance Records behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Maintenance Records contradicts a related document listed above.
- [ ] Maintenance Records is covered by at least one test referenced from `docs/testing/`.
- [ ] Maintenance Records requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Maintenance Records, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Maintenance Records that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Maintenance Records are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
