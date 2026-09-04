# Accessibility

> Canonical accessibility requirements, applying to every screen file.

## Requirements

1. All interactive elements reachable via keyboard alone, in a logical tab order matching
   visual layout (`04_layout.md`).
2. All `StateBadge` and `ClassificationBadge` components (`02_design_system.md`) convey their
   meaning via text label, not color alone — color-blind users must be able to distinguish
   FAILED from SUCCEEDED without relying on red/green.
3. All images/diagrams (evidence source previews, execution graph nodes) have text
   alternatives sufficient to understand the state being conveyed, even if not the full visual
   detail.
4. Minimum contrast ratio 4.5:1 for body text, 3:1 for large text/icons, per WCAG 2.1 AA.
5. Screen-reader announcements for state transitions that happen without user action (e.g. a
   Task moving to WAITING_APPROVAL while the user is reading something else) use ARIA live
   regions with `polite` priority — not `assertive`, to avoid interrupting reading.

## Test requirement

Each screen file's "Test requirements" (where present) includes at least one automated
accessibility check (axe-core or equivalent) as part of `testing/06_frontend_testing.md`.
