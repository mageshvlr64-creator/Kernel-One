# NetworkEvent

> JSON Schema for the wire/storage contract of **NetworkEvent**. Referenced by `docs/api/` and
> `docs/domain/`; this file is the single source for the shape, not a duplicate of either.

## NetworkEvent

```json
{
  "$id": "network-event.json",
  "title": "NetworkEvent",
  "type": "object",
  "required": [
    "timestamp",
    "check_name",
    "result"
  ],
  "properties": {
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "check_name": {
      "type": "string",
      "enum": [
        "internet",
        "external_dns",
        "external_http",
        "cloud_apis",
        "ui_to_api",
        "api_to_model",
        "api_to_vector_db",
        "agent_to_sandbox"
      ]
    },
    "result": {
      "type": "string",
      "enum": [
        "blocked",
        "ok",
        "degraded"
      ]
    },
    "detail": {
      "type": [
        "string",
        "null"
      ]
    }
  }
}
```


## Validation behavior

A request/object failing this schema is rejected with `INVALID_REQUEST`
(`docs/reference/01_error_codes.md`), including the specific field-level validation error(s),
before any business logic executes.
