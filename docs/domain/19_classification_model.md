# ClassificationLevel (reference, not a table)

> Canonical field-level definition. `docs/schemas/` holds the matching JSON Schema for any
> wire/storage representation of these fields; this file is the authoritative field list.

## Fields

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `level` | enum | yes | — | `PUBLIC` < `INTERNAL` < `CONFIDENTIAL` < `RESTRICTED` — see `reference/04_data_classification_levels.md` |

## Notes

Classification is a fixed, ordered enum used as a column type across `Document`, `User.clearance`, `Model.max_classification`, `Evidence` (inherited), and `Artifact` (computed) — it is not a separate persisted table. Full allowed-users/models/tools/export rules per level are defined once in `reference/04_data_classification_levels.md`.

## Ownership

This entity is owned and mutated only by the component named in its lifecycle description
above. Every other component reads it through the API/internal interface defined in
`docs/api/` and `docs/features/`, never by writing to its table directly.

## Audit behavior

Every insert/update/soft-delete on this entity's table produces a matching `AuditEvent`
(`schemas/15_audit_event_schema.md`) in the same transaction, per REQ-AUD-001.
