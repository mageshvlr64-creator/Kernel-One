# SystemConfiguration entry

> JSON Schema for the wire/storage contract of **SystemConfiguration entry**. Referenced by `docs/api/` and
> `docs/domain/`; this file is the single source for the shape, not a duplicate of either.

## ConfigurationEntry

```json
{
  "$id": "configuration-entry.json",
  "title": "ConfigurationEntry",
  "type": "object",
  "required": [
    "key",
    "value",
    "source"
  ],
  "properties": {
    "key": {
      "type": "string"
    },
    "value": {},
    "source": {
      "type": "string",
      "enum": [
        "env",
        "file",
        "default"
      ]
    },
    "is_secret": {
      "type": "boolean",
      "default": false
    }
  }
}
```


## Validation behavior

A request/object failing this schema is rejected with `INVALID_REQUEST`
(`docs/reference/01_error_codes.md`), including the specific field-level validation error(s),
before any business logic executes.
