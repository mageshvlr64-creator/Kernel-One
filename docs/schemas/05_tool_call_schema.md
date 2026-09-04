# ToolInvocationRequest / ToolInvocationResult

> JSON Schema for the wire/storage contract of **ToolInvocationRequest / ToolInvocationResult**. Referenced by `docs/api/` and
> `docs/domain/`; this file is the single source for the shape, not a duplicate of either.

## ToolInvocationRequest

```json
{
  "$id": "tool-invocation-request.json",
  "title": "ToolInvocationRequest",
  "type": "object",
  "required": [
    "tool_id",
    "task_id",
    "input"
  ],
  "properties": {
    "tool_id": {
      "type": "string"
    },
    "task_id": {
      "type": "string",
      "format": "uuid"
    },
    "input": {
      "type": "object",
      "description": "Validated against the tool-specific schema referenced in features/05_tool_gateway/03_tool_schema.md"
    }
  },
  "additionalProperties": false
}
```

## ToolInvocationResult

```json
{
  "$id": "tool-invocation-result.json",
  "title": "ToolInvocationResult",
  "type": "object",
  "required": [
    "id",
    "state"
  ],
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid"
    },
    "state": {
      "type": "string",
      "enum": [
        "CREATED",
        "AUTHORIZED",
        "RUNNING",
        "SUCCEEDED",
        "FAILED",
        "TIMEOUT",
        "CANCELLED"
      ]
    },
    "output": {
      "type": [
        "object",
        "null"
      ]
    },
    "error_code": {
      "type": [
        "string",
        "null"
      ],
      "description": "One of reference/01_error_codes.md"
    }
  }
}
```


## Validation behavior

A request/object failing this schema is rejected with `INVALID_REQUEST`
(`docs/reference/01_error_codes.md`), including the specific field-level validation error(s),
before any business logic executes.
