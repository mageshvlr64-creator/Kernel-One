# Responsive Behavior

> Canonical breakpoint behavior, referenced by `04_layout.md` and individual screens rather
> than redefined per screen.

## Breakpoints (defined once, in `04_layout.md`)

`mobile` < 640px · `tablet` 640–1024px · `desktop` > 1024px.

## Cross-cutting rules

- Side navigation (`04_layout.md`) collapses to an icon rail on `tablet`, and to a
  hamburger-triggered overlay on `mobile`.
- The Network Sovereignty indicator (`04_layout.md` top bar) remains visible at every
  breakpoint, including `mobile` — it is never hidden behind a menu, per REQ-NET-003's intent
  that the proof is always ambient.
- Data tables (Document list, User list, Audit log) switch from a multi-column table to a
  stacked card layout below `tablet`, preserving the same information (classification badge,
  state badge) rather than truncating fields silently.
- The Execution Graph (`08_execution_graph_ui.md`) is desktop-only in V1 — below `tablet`
  width, it renders a simplified linear step list instead of the graph visualization,
  explicitly noted as a V1 constraint rather than a bug.
