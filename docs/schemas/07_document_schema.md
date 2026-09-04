# DocumentUpload / Document

> JSON Schema for the wire/storage contract of **DocumentUpload / Document**. Referenced by `docs/api/` and
> `docs/domain/`; this file is the single source for the shape, not a duplicate of either.

## Document

```json
{
  "$id": "document.json",
  "title": "Document",
  "type": "object",
  "required": [
    "id",
    "filename",
    "mime_type",
    "classification",
    "state"
  ],
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid"
    },
    "filename": {
      "type": "string",
      "maxLength": 512
    },
    "mime_type": {
      "type": "string",
      "enum": [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "text/plain",
        "text/csv",
        "image/png",
        "image/jpeg"
      ]
    },
    "size_bytes": {
      "type": "integer",
      "minimum": 1,
      "maximum": 209715200
    },
    "sha256": {
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
        "UPLOADED",
        "VALIDATING",
        "EXTRACTING",
        "OCR",
        "INDEXING",
        "READY",
        "FAILED",
        "DELETED"
      ]
    }
  }
}
```


## Validation behavior

A request/object failing this schema is rejected with `INVALID_REQUEST`
(`docs/reference/01_error_codes.md`), including the specific field-level validation error(s),
before any business logic executes.
