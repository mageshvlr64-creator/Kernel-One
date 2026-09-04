# Role & Permission

> Canonical field-level definition. `docs/schemas/` holds the matching JSON Schema for any
> wire/storage representation of these fields; this file is the authoritative field list.

## Fields

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `id` | uuid | yes | generated | Role.id primary key |
| `name` | enum(Administrator,SecurityOfficer,Operator,Analyst,RestrictedUser,Auditor) | yes | — | fixed set — see `reference/05_permission_matrix.md`; not user-extensible in V1 |
| `description` | text | yes | — | human-readable |

## Notes

Role is a fixed enum in V1 (six roles, `reference/05_permission_matrix.md`), not a user-editable table — REQ-SEC-001 depends on the role set being closed and centrally defined. Permission is not a separate persisted row set in V1; permission evaluation is computed at request time by the policy engine (`features/21_policy_engine/`) against the static matrix plus the Policy table (see `16_policy_model.md`). A future V2 fine-grained/custom-role model is tracked in `later/`.

## Ownership

This entity is owned and mutated only by the component named in its lifecycle description
above. Every other component reads it through the API/internal interface defined in
`docs/api/` and `docs/features/`, never by writing to its table directly.

## Audit behavior

Every insert/update/soft-delete on this entity's table produces a matching `AuditEvent`
(`schemas/15_audit_event_schema.md`) in the same transaction, per REQ-AUD-001.
