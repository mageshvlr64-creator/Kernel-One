# Tool, ToolInvocation, TaskStep

> Canonical field-level definition. `docs/schemas/` holds the matching JSON Schema for any
> wire/storage representation of these fields; this file is the authoritative field list.

## Fields

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `tool_id` | text | yes | — | Tool.id, e.g. `filesystem.read`, `code_execution.run` |
| `name` | text | yes | — | human-readable |
| `version` | text | yes | — | semver |
| `input_schema_ref` | text | yes | — | pointer to `schemas/05_tool_call_schema.md` entry for this tool |
| `min_role` | enum per reference/05_permission_matrix.md | yes | — | minimum role able to invoke, before classification/approval conditions |
| `risk_level` | enum(low,medium,high) | yes | — | `reference/03_risk_levels.md` |
| `network_required` | boolean | yes | false | must be false for any tool usable in `air_gapped` mode |

## Notes

**ToolInvocation** (a row created per call): `id`, `tool_id` FK, `task_id` FK, `state` (see canonical state machine), `input` (jsonb, validated against the tool's input schema), `output` (jsonb, null until SUCCEEDED), `error_code` (nullable FK-like reference into `reference/01_error_codes.md`), `started_at`, `finished_at`. **TaskStep** (element of AgentRun.plan, not its own table): `{step_index, tool_id, input, depends_on: [step_index], status}` — stored inline in `AgentRun.plan` jsonb rather than a separate table, since a plan is immutable once validated (a replan creates a new AgentRun).

## Ownership

This entity is owned and mutated only by the component named in its lifecycle description
above. Every other component reads it through the API/internal interface defined in
`docs/api/` and `docs/features/`, never by writing to its table directly.

## Audit behavior

Every insert/update/soft-delete on this entity's table produces a matching `AuditEvent`
(`schemas/15_audit_event_schema.md`) in the same transaction, per REQ-AUD-001.
