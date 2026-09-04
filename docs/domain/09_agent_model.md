# AgentRun (internal to Task)

> Canonical field-level definition. `docs/schemas/` holds the matching JSON Schema for any
> wire/storage representation of these fields; this file is the authoritative field list.

## Fields

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `id` | uuid | yes | generated | Primary key |
| `task_id` | uuid FK → Task.id | yes | — | one AgentRun per Task attempt; a replan creates a new AgentRun row, not a mutation of the old one |
| `plan` | jsonb | yes | — | ordered array of TaskStep objects, see `10_tool_model.md` for TaskStep shape |
| `model_id` | text FK → Model.id | yes | — | model used for planning |
| `step_count` | integer | yes | 0 | incremented as steps execute; capped at `AGENT_MAX_STEPS` (CONFIG DEFAULT 20, REQ-FUNC-002) |
| `replan_count` | integer | yes | 0 | capped at `AGENT_MAX_REPLANS` (CONFIG DEFAULT 3) |
| `created_at` | timestamptz | yes | now() | immutable |

## Notes

Represents one planning+execution attempt within a Task's lifecycle. A Task may have multiple AgentRun rows if it replans (`features/04_agent_kernel/10_replanning.md`); the Task's own state (see state machine) reflects the latest AgentRun's status.

## Ownership

This entity is owned and mutated only by the component named in its lifecycle description
above. Every other component reads it through the API/internal interface defined in
`docs/api/` and `docs/features/`, never by writing to its table directly.

## Audit behavior

Every insert/update/soft-delete on this entity's table produces a matching `AuditEvent`
(`schemas/15_audit_event_schema.md`) in the same transaction, per REQ-AUD-001.
