# Documents API

> Directory: `docs/api/` · File: `11_documents_api.md` · Kind: **API contract**
> Part of the Sovereign AI Workbench (SIH26176) specification set.
> Previous: `10_model_router_api.md` · Next: `12_knowledge_api.md`

## Purpose

**Documents API** documents the exact HTTP/WS route(s), payloads, and status codes for "documents api" specifically. It is the single
place other documents point to when they need this fact, rather than each restating it.

## Definition

- **What it is:** Documents API is a named API contract within the `api/` category of the
  Sovereign AI Workbench specification.
- **Owner:** exactly one subsystem is authoritative for Documents API at runtime; every other
  component treats it as read-only input unless this document states otherwise.
- **Stability:** changes to Documents API require a corresponding entry in `docs/20_DECISION_LOG.md`
  and a check for consistency against every related document listed below.

## Detail

1. Documents API is fully specified without assuming internet access; it must work identically in
   air-gapped, restricted-network, and on-premise deployment modes
   (`docs/architecture/17_air_gapped_architecture.md`,
   `docs/architecture/18_restricted_network_architecture.md`,
   `docs/architecture/19_on_premise_architecture.md`).
2. Any consumer of Documents API enforces the same rule set described here — a feature that reads
   Documents API differently than documented here is a bug in that feature, not a variant.
3. Where Documents API interacts with permissions, the check is performed server-side against
   `docs/features/19_identity_and_rbac/05_permissions.md`; client input is never trusted for
   an authorization decision.
4. Where Documents API interacts with risk or exposure, treat it as **low**-sensitivity by
   default unless a specific feature file states otherwise.

## Interfaces and related documents

- **Related:**
- `docs/schemas/02_api_schema.md`
- `docs/api/26_error_contracts.md`

## Acceptance criteria

- [ ] Documents API behaves identically regardless of whether it is reached via the UI, the API, or
      an autonomous agent plan step.
- [ ] No implementation detail of Documents API contradicts a related document listed above.
- [ ] Documents API is covered by at least one test referenced from `docs/testing/`.
- [ ] Documents API requires no outbound network access to function correctly.

## Implementation notes for AI agents

Before changing anything related to Documents API, an implementing agent (see
`docs/14_AI_IMPLEMENTATION_PROTOCOL.md`) re-reads this file and every document under
"Related" above, and does not introduce a definition of Documents API that conflicts with what is
written here without first updating this document.

## Decision log pointer

Unresolved questions about Documents API are recorded in `docs/20_DECISION_LOG.md`, not resolved
silently inside code or left undocumented.
