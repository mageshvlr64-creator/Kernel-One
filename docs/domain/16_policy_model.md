# Policy

> Canonical field-level definition. `docs/schemas/` holds the matching JSON Schema for any
> wire/storage representation of these fields; this file is the authoritative field list.

## Fields

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `id` | uuid | yes | generated | Primary key |
| `name` | text | yes | — | unique |
| `scope` | enum(model,tool,document,network,export,approval) | yes | — | which policy category this row governs, see `features/21_policy_engine/` |
| `rule` | jsonb | yes | — | condition/action pairs; exact grammar in `schemas/13_policy_schema.md` |
| `priority` | integer | yes | 100 | lower evaluates first; see `features/21_policy_engine/04_policy_precedence.md` |
| `created_by` | uuid FK → User.id | yes | — | must hold Administrator role, REQ-SEC-001 |
| `created_at` | timestamptz | yes | now() | — |

## Notes

Policy rows are the operator-configurable layer sitting on top of the fixed `reference/05_permission_matrix.md` role table — the matrix defines the default/floor; a Policy row can only further restrict, never grant beyond the matrix (fail-closed composition, `features/21_policy_engine/03_policy_evaluation.md`).

## Ownership

This entity is owned and mutated only by the component named in its lifecycle description
above. Every other component reads it through the API/internal interface defined in
`docs/api/` and `docs/features/`, never by writing to its table directly.

## Audit behavior

Every insert/update/soft-delete on this entity's table produces a matching `AuditEvent`
(`schemas/15_audit_event_schema.md`) in the same transaction, per REQ-AUD-001.
