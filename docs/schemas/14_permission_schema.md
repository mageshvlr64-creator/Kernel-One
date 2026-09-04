# PermissionCheckRequest / PermissionCheckResult

> JSON Schema for the wire/storage contract of **PermissionCheckRequest / PermissionCheckResult**. Referenced by `docs/api/` and
> `docs/domain/`; this file is the single source for the shape, not a duplicate of either.

## PermissionCheckRequest

```json
{
  "$id": "permission-check-request.json",
  "title": "PermissionCheckRequest",
  "type": "object",
  "required": [
    "actor_id",
    "resource_type",
    "action"
  ],
  "properties": {
    "actor_id": {
      "type": "string",
      "format": "uuid"
    },
    "resource_type": {
      "type": "string"
    },
    "resource_id": {
      "type": [
        "string",
        "null"
      ],
      "format": "uuid"
    },
    "action": {
      "type": "string",
      "enum": [
        "create",
        "read",
        "update",
        "delete",
        "execute",
        "approve",
        "export"
      ]
    }
  }
}
```

## PermissionCheckResult

```json
{
  "$id": "permission-check-result.json",
  "title": "PermissionCheckResult",
  "type": "object",
  "required": [
    "allowed"
  ],
  "properties": {
    "allowed": {
      "type": "boolean"
    },
    "denying_rule": {
      "type": [
        "string",
        "null"
      ],
      "description": "Policy ID or 'role_matrix' if denied by the base role table"
    }
  }
}
```


## Validation behavior

A request/object failing this schema is rejected with `INVALID_REQUEST`
(`docs/reference/01_error_codes.md`), including the specific field-level validation error(s),
before any business logic executes.
