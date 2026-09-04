# Citation

> JSON Schema for the wire/storage contract of **Citation**. Referenced by `docs/api/` and
> `docs/domain/`; this file is the single source for the shape, not a duplicate of either.

## Citation

```json
{
  "$id": "citation.json",
  "title": "Citation",
  "type": "object",
  "required": [
    "evidence_id",
    "text_span_start",
    "text_span_end"
  ],
  "properties": {
    "evidence_id": {
      "type": "string",
      "format": "uuid"
    },
    "text_span_start": {
      "type": "integer",
      "minimum": 0
    },
    "text_span_end": {
      "type": "integer",
      "minimum": 0
    }
  }
}
```


## Validation behavior

A request/object failing this schema is rejected with `INVALID_REQUEST`
(`docs/reference/01_error_codes.md`), including the specific field-level validation error(s),
before any business logic executes.
