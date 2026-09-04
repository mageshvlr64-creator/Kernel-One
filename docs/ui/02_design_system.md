# Design System

> Canonical shared visual/interaction primitives. Screen files reference these; they do not
> define their own colors, spacing, or component variants.

## Tokens

| Token | Value | Usage |
|---|---|---|
| `color.status.success` | green | Sovereignty panel "blocked" (external) rows, SUCCEEDED states |
| `color.status.warning` | amber | WAITING_APPROVAL, WAITING_INPUT states |
| `color.status.danger` | red | FAILED, TIMEOUT, POLICY_DENIED, network monitor unreachable |
| `color.classification.public` | gray | Classification badge |
| `color.classification.internal` | blue | Classification badge |
| `color.classification.confidential` | orange | Classification badge |
| `color.classification.restricted` | red | Classification badge |
| `spacing.unit` | 8px | Base spacing grid |
| `radius.default` | 6px | Cards, buttons |

## Shared components

- **StateBadge** — renders any of the canonical state-machine values
  (`runtime/_state_machines_canonical.md`) with consistent color mapping.
- **ClassificationBadge** — renders `PUBLIC`/`INTERNAL`/`CONFIDENTIAL`/`RESTRICTED` with the
  classification color tokens above; used identically on Document, Artifact, and Task rows.
- **ErrorBanner** — renders an error using the exact `code`/`message` pair from
  `reference/01_error_codes.md`; never freeform error text.
- **CitationChip** — renders one Citation (`domain/13_evidence_model.md`), click-through to
  the Evidence Panel.
- **ApprovalGate** — wraps any control tied to a `risk=high` action; renders disabled with an
  "Approval required" tooltip until an `Approval.state=APPROVED` record exists.

## Rule

No screen file introduces a new color, spacing value, or one-off component variant without
adding it to this file first.
