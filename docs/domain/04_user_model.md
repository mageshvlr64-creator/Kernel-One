# User

> Canonical field-level definition. `docs/schemas/` holds the matching JSON Schema for any
> wire/storage representation of these fields; this file is the authoritative field list.

## Fields

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `id` | uuid | yes | generated | Primary key |
| `username` | text | yes | — | 3–64 chars, unique, lowercase-normalized |
| `display_name` | text | yes | — | 1–200 chars |
| `password_hash` | text | yes | — | argon2id; never returned by any API response |
| `role_id` | uuid FK → Role.id | yes | — | see domain/05_identity_model.md |
| `clearance` | enum(PUBLIC,INTERNAL,CONFIDENTIAL,RESTRICTED) | yes | INTERNAL | caller's maximum classification access, per `features/20_data_classification/` |
| `organization_id` | uuid FK → Organization.id | yes | — | on delete restrict |
| `is_active` | boolean | yes | true | false = login disabled, rows preserved for audit |
| `created_at` | timestamptz | yes | now() | immutable |
| `last_login_at` | timestamptz | no | null | updated on successful auth |

## Notes

Lifecycle: created (by Administrator) → active → deactivated (is_active=false, never hard-deleted, per REQ-AUD-001 audit-trail continuity). Every User row change produces a `user.updated` AuditEvent.

## Ownership

This entity is owned and mutated only by the component named in its lifecycle description
above. Every other component reads it through the API/internal interface defined in
`docs/api/` and `docs/features/`, never by writing to its table directly.

## Audit behavior

Every insert/update/soft-delete on this entity's table produces a matching `AuditEvent`
(`schemas/15_audit_event_schema.md`) in the same transaction, per REQ-AUD-001.
