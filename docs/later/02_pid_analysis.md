# P&ID Analysis (V2+)

> Structured successor to `industrial/08_p_and_id_intelligence.md`'s V1-aspirational
> description-only capability.

## What this would add over V1

- A symbol library (valves, pumps, instruments, line types) the vision pipeline matches
  against, producing a structured `{symbol_type, tag, location}` list rather than free-text
  description.
- Cross-referencing extracted tags against an equipment/tag database (would require a new
  domain entity, e.g. `EquipmentTag`, not currently in `domain/`).
- Consistency checking (e.g. a valve referenced in text but not found on the diagram, or vice
  versa) — genuinely useful, but requires the structured extraction above to exist first.

## Concrete prerequisites

1. A labeled P&ID symbol dataset for evaluation (`benchmarks/07_visual_benchmark.md` extension).
2. A decision on symbol library scope (industry-standard ISA symbols vs. a custom/reduced set)
   — this is a `DECISION REQUIRED` item to be added to `20_DECISION_LOG.md` when V2 planning
   begins, not decided speculatively here.
3. A new domain entity and schema for extracted symbols/tags, added to `domain/` and
   `schemas/` following the same field-level rigor as every V1 entity — not a jsonb blob
   bolted onto an existing table.

## Explicitly not a V1 stretch goal

Even if time permits during V1, this capability is not attempted — the risk of a
partially-working symbol extraction being mistaken for a reliable one outweighs the demo value,
per the same reasoning in `industrial/12_industrial_workflow_boundaries.md`.
