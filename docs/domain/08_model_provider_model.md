# Model, ModelDeployment, ModelCapability

> Canonical field-level definition. `docs/schemas/` holds the matching JSON Schema for any
> wire/storage representation of these fields; this file is the authoritative field list.

## Fields

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `id` | text | yes | — | Model.id — human-stable slug, e.g. `general-reasoning-7b` |
| `display_name` | text | yes | — | shown in UI model selector |
| `provider` | enum(vllm,ollama,llamacpp) | yes | — | which inference gateway adapter serves this model |
| `total_parameters_billions` | numeric | yes | — | REQ-AI-003: storage/VRAM sizing basis |
| `active_parameters_billions` | numeric | no | null | null for dense models; set for MoE — compute sizing basis only, never storage |
| `quantization` | text | yes | — | e.g. `4-bit-awq`, `fp16` |
| `context_window` | integer | yes | — | max tokens |
| `capabilities` | text[] | yes | — | subset of {coding, vision, tool_calling, structured_output, ocr_assist} |
| `max_classification` | enum(PUBLIC,INTERNAL,CONFIDENTIAL,RESTRICTED) | yes | INTERNAL | highest classification this model is approved to process — REQ-DATA-001/`MODEL_NOT_APPROVED` |
| `is_available` | boolean | yes | true | set false by health check when the backing runtime is unreachable |

## Notes

ModelDeployment (not separately tabled in V1) is represented by `is_available` + a runtime health-check cache; a full deployment-history table is a V2 item (`later/`). ModelCapability is the `capabilities` array plus `max_classification` on the Model row itself — capabilities are not a separate join table in V1 given the small number of models expected (see `07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md` reference registry).

## Ownership

This entity is owned and mutated only by the component named in its lifecycle description
above. Every other component reads it through the API/internal interface defined in
`docs/api/` and `docs/features/`, never by writing to its table directly.

## Audit behavior

Every insert/update/soft-delete on this entity's table produces a matching `AuditEvent`
(`schemas/15_audit_event_schema.md`) in the same transaction, per REQ-AUD-001.
