# Workspace

> Canonical field-level definition. `docs/schemas/` holds the matching JSON Schema for any
> wire/storage representation of these fields; this file is the authoritative field list.

## Fields

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `id` | uuid | yes | generated | Primary key |
| `name` | text | yes | — | 1–200 chars, unique per organization |
| `organization_id` | uuid FK → Organization.id | yes | — | on delete restrict |
| `default_classification` | enum(PUBLIC,INTERNAL,CONFIDENTIAL,RESTRICTED) | yes | INTERNAL | see reference/04_data_classification_levels.md |
| `created_at` | timestamptz | yes | now() | immutable |
| `updated_at` | timestamptz | yes | now() | auto-updated on write |
| `deleted_at` | timestamptz | no | null | soft-delete marker; null = active |

## Notes

A Workspace scopes Tasks, Documents, and Artifacts for one team/project within an Organization. Lifecycle: created → active → (soft) deleted. Retention: soft-deleted for 30 days (CONFIG DEFAULT) before a background job purges dependent rows per `operations/07_storage_operations.md`.

## Ownership

This entity is owned and mutated only by the component named in its lifecycle description
above. Every other component reads it through the API/internal interface defined in
`docs/api/` and `docs/features/`, never by writing to its table directly.

## Audit behavior

Every insert/update/soft-delete on this entity's table produces a matching `AuditEvent`
(`schemas/15_audit_event_schema.md`) in the same transaction, per REQ-AUD-001.
