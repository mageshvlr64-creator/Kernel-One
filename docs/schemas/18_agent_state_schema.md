# AgentRun state machine (machine-readable)

> JSON Schema for the wire/storage contract of **AgentRun state machine (machine-readable)**. Referenced by `docs/api/` and
> `docs/domain/`; this file is the single source for the shape, not a duplicate of either.

## StateMachine

```json
{
  "$id": "state-machine.json",
  "title": "StateMachine",
  "type": "object",
  "required": [
    "entity",
    "states",
    "transitions"
  ],
  "properties": {
    "entity": {
      "type": "string"
    },
    "states": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "transitions": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [
          "from",
          "to",
          "owner",
          "audit_event"
        ],
        "properties": {
          "from": {
            "type": "string"
          },
          "to": {
            "type": "string"
          },
          "owner": {
            "type": "string"
          },
          "audit_event": {
            "type": "string"
          }
        }
      }
    }
  }
}
```


## Validation behavior

A request/object failing this schema is rejected with `INVALID_REQUEST`
(`docs/reference/01_error_codes.md`), including the specific field-level validation error(s),
before any business logic executes.
