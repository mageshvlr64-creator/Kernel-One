# ApprovalDecision / Approval

> JSON Schema for the wire/storage contract of **ApprovalDecision / Approval**. Referenced by `docs/api/` and
> `docs/domain/`; this file is the single source for the shape, not a duplicate of either.

## ApprovalDecision

```json
{
  "$id": "approval-decision.json",
  "title": "ApprovalDecision",
  "type": "object",
  "required": [
    "approval_id",
    "decision"
  ],
  "properties": {
    "approval_id": {
      "type": "string",
      "format": "uuid"
    },
    "decision": {
      "type": "string",
      "enum": [
        "approved",
        "rejected"
      ]
    },
    "reason": {
      "type": "string",
      "description": "Required if decision=rejected"
    }
  }
}
```

## Approval

```json
{
  "$id": "approval.json",
  "title": "Approval",
  "type": "object",
  "required": [
    "id",
    "task_id",
    "action_type",
    "state",
    "expires_at"
  ],
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid"
    },
    "task_id": {
      "type": "string",
      "format": "uuid"
    },
    "action_type": {
      "type": "string"
    },
    "state": {
      "type": "string",
      "enum": [
        "REQUESTED",
        "APPROVED",
        "REJECTED",
        "EXPIRED",
        "CANCELLED"
      ]
    },
    "expires_at": {
      "type": "string",
      "format": "date-time"
    }
  }
}
```


## Validation behavior

A request/object failing this schema is rejected with `INVALID_REQUEST`
(`docs/reference/01_error_codes.md`), including the specific field-level validation error(s),
before any business logic executes.
