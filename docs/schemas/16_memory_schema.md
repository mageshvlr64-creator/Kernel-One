# MemoryEntry

> JSON Schema for the wire/storage contract of **MemoryEntry**. Referenced by `docs/api/` and
> `docs/domain/`; this file is the single source for the shape, not a duplicate of either.

## MemoryEntry

```json
{
  "$id": "memory-entry.json",
  "title": "MemoryEntry",
  "type": "object",
  "required": [
    "id",
    "scope",
    "scope_id",
    "content"
  ],
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid"
    },
    "scope": {
      "type": "string",
      "enum": [
        "conversation",
        "task",
        "workspace"
      ]
    },
    "scope_id": {
      "type": "string",
      "format": "uuid"
    },
    "content": {
      "type": "string"
    },
    "expires_at": {
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
