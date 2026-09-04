# Artifact

> JSON Schema for the wire/storage contract of **Artifact**. Referenced by `docs/api/` and
> `docs/domain/`; this file is the single source for the shape, not a duplicate of either.

## Artifact

```json
{
  "$id": "artifact.json",
  "title": "Artifact",
  "type": "object",
  "required": [
    "id",
    "task_id",
    "type",
    "state",
    "classification"
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
    "type": {
      "type": "string",
      "enum": [
        "docx",
        "pptx",
        "xlsx",
        "pdf",
        "csv",
        "json",
        "markdown",
        "code"
      ]
    },
    "filename": {
      "type": "string"
    },
    "checksum": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
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
    "state": {
      "type": "string",
      "enum": [
        "CREATED",
        "VALIDATING",
        "READY",
        "APPROVED",
        "REJECTED",
        "EXPORTED",
        "DELETED",
        "FAILED"
      ]
    },
    "evidence_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "uuid"
      }
    }
  }
}
```


## Validation behavior

A request/object failing this schema is rejected with `INVALID_REQUEST`
(`docs/reference/01_error_codes.md`), including the specific field-level validation error(s),
before any business logic executes.
