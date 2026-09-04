# Task

> Canonical field-level definition. `docs/schemas/` holds the matching JSON Schema for any
> wire/storage representation of these fields; this file is the authoritative field list.

## Fields

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `id` | uuid | yes | generated | Primary key |
| `workspace_id` | uuid FK → Workspace.id | yes | — | on delete restrict |
| `created_by` | uuid FK → User.id | yes | — | on delete restrict |
| `title` | text | yes | — | derived from the first user message if not explicitly set |
| `state` | enum per docs/runtime/_state_machines_canonical.md#task | yes | CREATED | see canonical Task state machine |
| `classification` | enum(PUBLIC,INTERNAL,CONFIDENTIAL,RESTRICTED) | yes | computed | max classification of any Document/Evidence the task touches (REQ-DATA-001) |
| `conversation_id` | uuid FK → Conversation.id | yes | — | see `12_execution_model.md` |
| `created_at` | timestamptz | yes | now() | immutable |
| `completed_at` | timestamptz | no | null | set on COMPLETED/FAILED/CANCELLED |

## Notes

See `domain/12_execution_model.md` for Conversation/Message, and `09_agent_model.md` for the AgentRun(s) that actually execute a Task's plan. State transitions and every transition's audit event are defined once in `docs/runtime/_state_machines_canonical.md#task`.

## Ownership

This entity is owned and mutated only by the component named in its lifecycle description
above. Every other component reads it through the API/internal interface defined in
`docs/api/` and `docs/features/`, never by writing to its table directly.

## Audit behavior

Every insert/update/soft-delete on this entity's table produces a matching `AuditEvent`
(`schemas/15_audit_event_schema.md`) in the same transaction, per REQ-AUD-001.
