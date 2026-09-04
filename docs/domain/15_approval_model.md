# Approval

> Canonical field-level definition. `docs/schemas/` holds the matching JSON Schema for any
> wire/storage representation of these fields; this file is the authoritative field list.

## Fields

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `id` | uuid | yes | generated | Primary key |
| `task_id` | uuid FK → Task.id | yes | — | — |
| `action_type` | text | yes | — | e.g. `tool_invocation.execute`, `artifact.export` |
| `action_ref_id` | uuid | yes | — | ID of the ToolInvocation/Artifact/etc. being gated |
| `requested_by` | uuid FK → User.id | yes | — | usually the agent kernel acting on behalf of the task's owner |
| `state` | enum per docs/runtime/_state_machines_canonical.md#approval | yes | REQUESTED | — |
| `decided_by` | uuid FK → User.id | no | null | must hold Administrator or SecurityOfficer role |
| `decided_at` | timestamptz | no | null | — |
| `expires_at` | timestamptz | yes | requested_at + 24h | CONFIG DEFAULT; see `16_human_approval/11_expired_approvals.md` |
| `reason` | text | no | null | required if state = REJECTED |

## Notes

See `docs/runtime/_state_machines_canonical.md#approval` for full transition table including the re-approval rule (editing the gated action after REQUESTED cancels this row and requires a new one).

## Ownership

This entity is owned and mutated only by the component named in its lifecycle description
above. Every other component reads it through the API/internal interface defined in
`docs/api/` and `docs/features/`, never by writing to its table directly.

## Audit behavior

Every insert/update/soft-delete on this entity's table produces a matching `AuditEvent`
(`schemas/15_audit_event_schema.md`) in the same transaction, per REQ-AUD-001.
