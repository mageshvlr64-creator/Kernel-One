# Empty States

> Canonical empty-state copy and behavior, referenced by each screen's own "States" section
> rather than redefined per screen.

## Rule

Every list/collection view distinguishes:

1. **Genuinely empty** (e.g. "No tasks yet") — friendly copy plus a primary action to create
   the first item, per screen.
2. **Empty due to filtering** (e.g. classification filter hides all results) — copy states the
   filter is active and offers to clear it, distinct from "there is nothing here at all."
3. **Empty due to permission** (e.g. a Restricted User sees zero tools in the tool list) — this
   is not framed as an error; it renders the same as case 1 but without a "create" affordance
   the user isn't permitted to use.

## Notable case — Evidence Panel (REQ-FUNC-005)

An agent answer with zero attached Evidence is not a normal empty state — it should not occur
under REQ-FUNC-005's "no unsupported claims" rule, so this specific empty state renders with a
distinct visual flag (not danger-red, but not the friendly neutral empty state either) and is
worth investigating if seen in production, per `features/14_evidence_and_provenance/09_unsupported_claim_detection.md`.
