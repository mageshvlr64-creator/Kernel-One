# AuditEvent

> Canonical field-level definition. `docs/schemas/` holds the matching JSON Schema for any
> wire/storage representation of these fields; this file is the authoritative field list.

## Fields

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `event_id` | uuid | yes | generated | Primary key; see full field list in `schemas/15_audit_event_schema.md` |

## Notes

Full field-by-field definition lives once in `schemas/15_audit_event_schema.md` (the canonical JSON Schema) — this domain file exists only to place `AuditEvent` in the entity-relationship picture: it references `actor_id` (User), `resource_id` (polymorphic — Task/Document/Artifact/etc.), and `correlation_id` (groups events for one end-to-end request). It is never redefined here.

## Ownership

This entity is owned and mutated only by the component named in its lifecycle description
above. Every other component reads it through the API/internal interface defined in
`docs/api/` and `docs/features/`, never by writing to its table directly.

## Audit behavior

Every insert/update/soft-delete on this entity's table produces a matching `AuditEvent`
(`schemas/15_audit_event_schema.md`) in the same transaction, per REQ-AUD-001.
