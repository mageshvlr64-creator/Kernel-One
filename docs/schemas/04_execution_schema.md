# Plan / PlanStep

> JSON Schema for the wire/storage contract of **Plan / PlanStep**. Referenced by `docs/api/` and
> `docs/domain/`; this file is the single source for the shape, not a duplicate of either.

## Plan

```json
{
  "$id": "plan.json",
  "title": "Plan",
  "type": "object",
  "required": [
    "steps"
  ],
  "properties": {
    "steps": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/PlanStep"
      },
      "maxItems": 20,
      "description": "AGENT_MAX_STEPS=20, CONFIG DEFAULT"
    }
  },
  "$defs": {
    "PlanStep": {
      "type": "object",
      "required": [
        "step_index",
        "tool_id",
        "input"
      ],
      "properties": {
        "step_index": {
          "type": "integer",
          "minimum": 0
        },
        "tool_id": {
          "type": "string"
        },
        "input": {
          "type": "object"
        },
        "depends_on": {
          "type": "array",
          "items": {
            "type": "integer"
          }
        },
        "status": {
          "type": "string",
          "enum": [
            "pending",
            "running",
            "succeeded",
            "failed",
            "skipped"
          ]
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
