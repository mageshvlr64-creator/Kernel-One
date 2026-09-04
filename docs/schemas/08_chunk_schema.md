# DocumentChunk

> JSON Schema for the wire/storage contract of **DocumentChunk**. Referenced by `docs/api/` and
> `docs/domain/`; this file is the single source for the shape, not a duplicate of either.

## DocumentChunk

```json
{
  "$id": "document-chunk.json",
  "title": "DocumentChunk",
  "type": "object",
  "required": [
    "id",
    "document_id",
    "chunk_index",
    "text",
    "embedding"
  ],
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid"
    },
    "document_id": {
      "type": "string",
      "format": "uuid"
    },
    "chunk_index": {
      "type": "integer",
      "minimum": 0
    },
    "page_number": {
      "type": [
        "integer",
        "null"
      ]
    },
    "bbox": {
      "type": [
        "array",
        "null"
      ],
      "items": {
        "type": "number"
      },
      "minItems": 4,
      "maxItems": 4
    },
    "text": {
      "type": "string"
    },
    "embedding": {
      "type": "array",
      "items": {
        "type": "number"
      },
      "minItems": 768,
      "maxItems": 768
    },
    "ocr_confidence": {
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
