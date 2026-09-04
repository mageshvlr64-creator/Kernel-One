# Audit Event Schema (Canonical)

> **Canonical owner** of the `AuditEvent` shape. Every feature that emits audit events uses
> exactly this schema. No feature invents its own audit event field set.

## JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://sovereign-workbench.local/schemas/audit-event.json",
  "title": "AuditEvent",
  "type": "object",
  "required": [
    "event_id", "timestamp", "event_type", "actor_id", "session_id",
    "action", "resource_type", "result"
  ],
  "properties": {
    "event_id":        { "type": "string", "format": "uuid" },
    "timestamp":        { "type": "string", "format": "date-time" },
    "event_type":       { "type": "string", "description": "dot.separated event name, e.g. 'task.created', 'tool_invocation.authorized'" },
    "actor_id":         { "type": "string", "format": "uuid", "description": "User ID; 'system' for scheduled/internal jobs" },
    "session_id":       { "type": ["string", "null"], "format": "uuid" },
    "correlation_id":   { "type": ["string", "null"], "format": "uuid", "description": "Groups events from one end-to-end request/task" },
    "task_id":          { "type": ["string", "null"], "format": "uuid" },
    "action":           { "type": "string", "enum": ["create", "read", "update", "delete", "execute", "approve", "reject", "export", "login", "logout"] },
    "resource_type":    { "type": "string", "description": "e.g. Task, Document, ToolInvocation, Artifact, User, Policy" },
    "resource_id":      { "type": ["string", "null"], "format": "uuid" },
    "classification":   { "type": ["string", "null"], "enum": ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED", null] },
    "decision":         { "type": ["string", "null"], "enum": ["allowed", "denied", null], "description": "Populated for authorization-relevant events" },
    "result":           { "type": "string", "enum": ["success", "error", "denied"] },
    "error_code":       { "type": ["string", "null"], "description": "One of reference/01_error_codes.md; required if result != 'success'" },
    "reason":           { "type": ["string", "null"], "description": "Human-readable reason, especially for denials/rejections" },
    "tool_id":          { "type": ["string", "null"] },
    "model_id":         { "type": ["string", "null"] },
    "artifact_id":      { "type": ["string", "null"] },
    "source_interface": { "type": ["string", "null"], "description": "e.g. 'api', 'ui', 'agent_kernel', 'scheduled_job'" },
    "source_ip":        { "type": ["string", "null"], "description": "Populated for API-originated events only; null for internal calls" },
    "payload_hash":     { "type": ["string", "null"], "description": "SHA-256 of the request payload; never the raw payload if it may contain sensitive content" },
    "prev_event_hash":  { "type": "string", "description": "SHA-256 of the previous audit event, forming a tamper-evident chain per REQ-SEC-005" }
  },
  "additionalProperties": false
}
```

## Storage rules (REQ-SEC-005, REQ-AUD-001)

- `audit_events` table grants `INSERT` only to the application's service role — no `UPDATE`,
  no `DELETE`, for any application-level database credential.
- `prev_event_hash` is computed and verified at write time; a background integrity job
  (`operations/05_log_management.md`) periodically re-walks the chain and alerts on mismatch.
- Retention: indefinite by default (no automatic deletion); an operator-triggered archival
  procedure exists in `operations/08_backup_operations.md` but does not delete the live table.

## Example event

```json
{
  "event_id": "5b9c9e3a-4b0a-4c9f-9a1b-1e2f3a4b5c6d",
  "timestamp": "2026-09-02T10:15:30Z",
  "event_type": "tool_invocation.authorized",
  "actor_id": "8f14e45f-ceea-4bce-8ba7-b3d67a1cd5f0",
  "session_id": "2c9e3a1b-8f4d-4e6a-9c1d-7b6a5e4f3d2c",
  "correlation_id": "9d8c7b6a-5e4f-3d2c-1b0a-9f8e7d6c5b4a",
  "task_id": "1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "action": "execute",
  "resource_type": "ToolInvocation",
  "resource_id": "3f2e1d0c-9b8a-7f6e-5d4c-3b2a1f0e9d8c",
  "classification": "INTERNAL",
  "decision": "allowed",
  "result": "success",
  "error_code": null,
  "reason": null,
  "tool_id": "filesystem.read",
  "model_id": null,
  "artifact_id": null,
  "source_interface": "agent_kernel",
  "source_ip": null,
  "payload_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "prev_event_hash": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"
}
```

## How feature documents use this file

A feature's "Audit requirements" section states only: the `event_type` value(s) it emits and
which optional fields it populates (e.g. `tool_id`, `model_id`, `artifact_id`) — it references
this file for the full field list rather than repeating it.
