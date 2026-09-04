# Loading States

> Canonical loading-state rendering rules.

## Rule

Every screen distinguishes three loading situations, never collapsing them into one generic
spinner:

1. **Initial load** (no data yet) — skeleton placeholders matching the eventual layout
   (`02_design_system.md` shared skeleton components), not a centered spinner, so the page
   doesn't visually "jump" once data arrives.
2. **Background refresh** (data already shown, re-fetching) — a subtle inline indicator (e.g.
   a small spinner in the top bar), the existing content stays visible and interactive.
3. **Action-in-flight** (user just clicked something) — the triggering control shows its own
   inline spinner and is disabled; the rest of the screen remains interactive unless the action
   is page-level (e.g. document upload).

## Long-running operations

Operations expected to exceed 2 seconds (document ingestion, artifact generation, agent
planning) show a progress indicator tied to the actual state machine transition
(`runtime/_state_machines_canonical.md`), e.g. "Extracting text… → Running OCR… → Indexing…"
rather than an indeterminate spinner for the whole duration.
