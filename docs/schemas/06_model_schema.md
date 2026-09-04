# Model / ModelCapability

> JSON Schema for the wire/storage contract of **Model / ModelCapability**. Referenced by `docs/api/` and
> `docs/domain/`; this file is the single source for the shape, not a duplicate of either.

## Model

```json
{
  "$id": "model.json",
  "title": "Model",
  "type": "object",
  "required": [
    "id",
    "provider",
    "total_parameters_billions",
    "context_window",
    "capabilities",
    "max_classification"
  ],
  "properties": {
    "id": {
      "type": "string"
    },
    "display_name": {
      "type": "string"
    },
    "provider": {
      "type": "string",
      "enum": [
        "vllm",
        "ollama",
        "llamacpp"
      ]
    },
    "total_parameters_billions": {
      "type": "number",
      "minimum": 0
    },
    "active_parameters_billions": {
      "type": [
        "number",
        "null"
      ],
      "minimum": 0,
      "description": "MoE only; compute sizing, never storage sizing (REQ-AI-003)"
    },
    "quantization": {
      "type": "string"
    },
    "context_window": {
      "type": "integer",
      "minimum": 1
    },
    "capabilities": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": [
          "coding",
          "vision",
          "tool_calling",
          "structured_output",
          "ocr_assist"
        ]
      }
    },
    "max_classification": {
      "type": "string",
      "enum": [
        "PUBLIC",
        "INTERNAL",
        "CONFIDENTIAL",
        "RESTRICTED"
      ]
    },
    "is_available": {
      "type": "boolean"
    }
  }
}
```


## Validation behavior

A request/object failing this schema is rejected with `INVALID_REQUEST`
(`docs/reference/01_error_codes.md`), including the specific field-level validation error(s),
before any business logic executes.
