# MemoryEntry

> Canonical field-level definition. `docs/schemas/` holds the matching JSON Schema for any
> wire/storage representation of these fields; this file is the authoritative field list.

## Fields

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `id` | uuid | yes | generated | Primary key |
| `scope` | enum(conversation,task,workspace) | yes | — | see `features/22_agent_memory/` |
| `scope_id` | uuid | yes | — | Conversation.id / Task.id / Workspace.id depending on scope |
| `content` | text | yes | — | summarized context, not raw message replay |
| `created_at` | timestamptz | yes | now() | — |
| `expires_at` | timestamptz | no | null | CONFIG DEFAULT retention per scope, `features/22_agent_memory/08_memory_expiration.md` |

## Notes

MemoryEntry rows are read-filtered by the same classification/workspace rules as Documents (`features/22_agent_memory/09_memory_permissions.md`) — memory is not an authorization bypass.

## Ownership

This entity is owned and mutated only by the component named in its lifecycle description
above. Every other component reads it through the API/internal interface defined in
`docs/api/` and `docs/features/`, never by writing to its table directly.

## Audit behavior

Every insert/update/soft-delete on this entity's table produces a matching `AuditEvent`
(`schemas/15_audit_event_schema.md`) in the same transaction, per REQ-AUD-001.
