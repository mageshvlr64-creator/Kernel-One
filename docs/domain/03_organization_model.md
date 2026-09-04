# Organization

> Canonical field-level definition. `docs/schemas/` holds the matching JSON Schema for any
> wire/storage representation of these fields; this file is the authoritative field list.

## Fields

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `id` | uuid | yes | generated | Primary key |
| `name` | text | yes | — | 1–200 chars, unique |
| `network_mode` | enum(air_gapped,restricted,on_premise) | yes | air_gapped | REQ-NET-002; deployment-wide, not per-workspace |
| `created_at` | timestamptz | yes | now() | immutable |

## Notes

The top-level tenant boundary. V1 assumes exactly one Organization per deployment (single-tenant); the column exists for schema stability into V2 multi-tenant scenarios, which are out of V1 scope (`02_SCOPE_AND_NON_GOALS.md`).

## Ownership

This entity is owned and mutated only by the component named in its lifecycle description
above. Every other component reads it through the API/internal interface defined in
`docs/api/` and `docs/features/`, never by writing to its table directly.

## Audit behavior

Every insert/update/soft-delete on this entity's table produces a matching `AuditEvent`
(`schemas/15_audit_event_schema.md`) in the same transaction, per REQ-AUD-001.
