# TaskRequest / Task

> JSON Schema for the wire/storage contract of **TaskRequest / Task**. Referenced by `docs/api/` and
> `docs/domain/`; this file is the single source for the shape, not a duplicate of either.

## TaskRequest

```json
{
  "$id": "task-request.json",
  "title": "TaskRequest",
  "type": "object",
  "required": [
    "workspace_id",
    "conversation_id",
    "prompt"
  ],
  "properties": {
    "workspace_id": {
      "type": "string",
      "format": "uuid"
    },
    "conversation_id": {
      "type": "string",
      "format": "uuid"
    },
    "prompt": {
      "type": "string",
      "minLength": 1,
      "maxLength": 20000
    },
    "attachments": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "uuid"
      },
      "description": "Document IDs already uploaded"
    },
    "model_hint": {
      "type": [
        "string",
        "null"
      ],
      "description": "Optional capability slot override, e.g. 'coding'"
    }
  },
  "additionalProperties": false
}
```

## Task

```json
{
  "$id": "task.json",
  "title": "Task",
  "type": "object",
  "required": [
    "id",
    "workspace_id",
    "state",
    "classification",
    "created_at"
  ],
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid"
    },
    "workspace_id": {
      "type": "string",
      "format": "uuid"
    },
    "title": {
      "type": "string"
    },
    "state": {
      "type": "string",
      "enum": [
        "CREATED",
        "PLANNING",
        "WAITING_APPROVAL",
        "EXECUTING",
        "WAITING_INPUT",
        "COMPLETED",
        "FAILED",
        "CANCELLED"
      ]
    },
    "classification": {
      "type": "string",
      "enum": [
        "PUBLIC",
        "INTERNAL",
        "CONFIDENTIAL",
        "RESTRICTED"
      ]
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "completed_at": {
      "type": [
        "string",
        "null"
      ],
      "format": "date-time"
    }
  }
}
```


## Validation behavior

A request/object failing this schema is rejected with `INVALID_REQUEST`
(`docs/reference/01_error_codes.md`), including the specific field-level validation error(s),
before any business logic executes.
