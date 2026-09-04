# Policy

> JSON Schema for the wire/storage contract of **Policy**. Referenced by `docs/api/` and
> `docs/domain/`; this file is the single source for the shape, not a duplicate of either.

## Policy

```json
{
  "$id": "policy.json",
  "title": "Policy",
  "type": "object",
  "required": [
    "id",
    "name",
    "scope",
    "rule",
    "priority"
  ],
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid"
    },
    "name": {
      "type": "string"
    },
    "scope": {
      "type": "string",
      "enum": [
        "model",
        "tool",
        "document",
        "network",
        "export",
        "approval"
      ]
    },
    "rule": {
      "type": "object",
      "required": [
        "condition",
        "effect"
      ],
      "properties": {
        "condition": {
          "type": "object",
          "description": "e.g. {\"classification_gte\": \"CONFIDENTIAL\"}"
        },
        "effect": {
          "type": "string",
          "enum": [
            "deny",
            "require_approval",
            "allow"
          ]
        }
      }
    },
    "priority": {
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
