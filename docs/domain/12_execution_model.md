# Conversation, Message

> Canonical field-level definition. `docs/schemas/` holds the matching JSON Schema for any
> wire/storage representation of these fields; this file is the authoritative field list.

## Fields

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `id` | uuid | yes | generated | Conversation.id primary key |
| `workspace_id` | uuid FK → Workspace.id | yes | — | — |
| `user_id` | uuid FK → User.id | yes | — | — |
| `created_at` | timestamptz | yes | now() | immutable |

## Notes

**Message**: `id`, `conversation_id` FK, `role` (`enum(user,assistant,system,tool)`), `content` (text or jsonb for structured tool messages), `model_id` (nullable FK, set for assistant messages), `created_at`. A Conversation groups Messages across one or more Tasks (a user may issue several tasks within one chat thread); `Task.conversation_id` links back.

## Ownership

This entity is owned and mutated only by the component named in its lifecycle description
above. Every other component reads it through the API/internal interface defined in
`docs/api/` and `docs/features/`, never by writing to its table directly.

## Audit behavior

Every insert/update/soft-delete on this entity's table produces a matching `AuditEvent`
(`schemas/15_audit_event_schema.md`) in the same transaction, per REQ-AUD-001.
