# Layout

> Canonical page-frame structure every screen uses.

## Frame

```
+----------------------------------------------------------+
| Top bar: workspace selector | user menu | network status  |
+--------+---------------------------------------------------+
| Side   | Screen content (see ui/03_navigation.md route map)|
| nav    |                                                    |
|        |                                                    |
+--------+---------------------------------------------------+
```

- **Top bar** always shows a compact Network Sovereignty indicator (green/red dot, linking to
  the full `13_network_panel.md`) — visible from every screen, per REQ-NET-003's intent that
  sovereignty proof should be ambient, not something the user has to navigate to find.
- **Side nav** collapses to icons only below 1024px viewport width (`22_responsive_behavior.md`).
- **Content area** never exceeds 1200px max-width on large screens (readability), left-aligned,
  not centered with large empty margins.

## Responsive breakpoints

Defined once here: `mobile` < 640px, `tablet` 640–1024px, `desktop` > 1024px. Every screen
file's layout notes reference these three names rather than raw pixel values.
