# Cancellation Policy

> User-initiated cancellation, distinct from timeout (system-initiated) or failure
> (error-initiated).

## Cancellable operations

| Operation | Cancellable? | Effect |
|---|---|---|
| Task (any non-terminal state) | Yes (`POST /api/v1/tasks/{id}/cancel`) | Task → `CANCELLED`; any in-flight ToolInvocation for it → `CANCELLED` |
| Individual ToolInvocation | Not directly cancellable via API in V1 — cancellation happens at the Task level, cascading down | Cancelling the parent Task is the only V1-supported mechanism |
| Approval request | Yes, by the requester, before a decision is made | Approval → `CANCELLED` (distinct from `REJECTED`, which requires an approver's decision) |
| Document ingestion | Not cancellable mid-pipeline in V1 — must complete or fail naturally | A future V2 refinement could add this; not scoped for V1 |

## Rule

Cancellation always produces an audit event (`task.cancelled`, `approval.cancelled`) — a
cancelled operation is not simply "forgotten," it's a recorded outcome like any other
terminal state (REQ-AUD-001 makes no exception for user-initiated stops).
