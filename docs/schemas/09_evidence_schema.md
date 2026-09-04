# Evidence

> JSON Schema for the wire/storage contract of **Evidence**. Referenced by `docs/api/` and
> `docs/domain/`; this file is the single source for the shape, not a duplicate of either.

## Evidence

```json
{
  "$id": "evidence.json",
  "title": "Evidence",
  "type": "object",
  "required": [
    "id",
    "source_document_id",
    "chunk_id",
    "source_hash",
    "retrieval_method"
  ],
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid"
    },
    "source_document_id": {
      "type": "string",
      "format": "uuid"
    },
    "document_version": {
      "type": "integer"
    },
    "chunk_id": {
      "type": "string",
      "format": "uuid"
    },
    "page_number": {
      "type": [
        "integer",
        "null"
      ]
    },
    "source_hash": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    },
    "retrieval_method": {
      "type": "string",
      "enum": [
        "vector",
        "keyword",
        "hybrid"
      ]
    },
    "confidence": {
      "type": [
        "number",
        "null"
      ],
      "minimum": 0,
      "maximum": 1
    }
  }
}
```


## Validation behavior

A request/object failing this schema is rejected with `INVALID_REQUEST`
(`docs/reference/01_error_codes.md`), including the specific field-level validation error(s),
before any business logic executes.
