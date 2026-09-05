# Changelog

> **If you are an AI coding agent: read this before you write code, and append to it before
> you finish your turn.** This file is the running record of what's actually been built,
> by whom, and why — not just what the `docs/` spec says should exist. `docs/` describes the
> target; this file describes progress toward it. They will disagree sometimes (a feature
> spec'd but not yet built, a decision made during implementation that refines the spec) — that
> disagreement is exactly what this file is for tracking.

## How to use this file

1. Before starting work, check `TEAM.md` and confirm which character you're building as.
2. Check this file for the most recent entry under your character's name, so you know what
   you (or the last session building as your character) left off at.
3. Do the work, scoped to your character's owned files per `TEAM.md`.
4. Before ending your turn, append a new entry below, under today's date, in this format:

```
### [Character N — Name] YYYY-MM-DD

**Built/changed:**
- <specific file or capability, one line each>

**Status:** <what works now that didn't before, in plain language>

**Blocked on / depends on:** <if anything you needed from another character isn't ready yet>

**Next:** <what the next session on this character should pick up — optional, only if it's
not obvious from the docs/ spec itself>
```

5. Never edit a previous entry to "clean it up" — this is a log, not a summary document. If
   something in an old entry turned out to be wrong, add a new entry that says so; don't
   rewrite history.
6. Never write an entry claiming something works if you haven't actually run/tested it this
   session — "implemented, not yet tested" is an honest and acceptable status; "done" when it
   isn't is not.

## Format notes

- One `###` entry per work session per character, even if multiple sessions happen the same
  day — don't merge same-day entries from different sessions into one.
- Entries are append-only, newest at the bottom (chronological, not reverse-chronological) —
  this makes each character's own history readable top-to-bottom as a build log, matching
  `docs/08_BUILD_PHASES.md`'s phase ordering.
- If your change touches a shared contract (`docs/api/`, `docs/schemas/`, `docs/domain/`
  outside your carve-outs — see `TEAM.md`'s "Shared contracts" table), say so explicitly in
  the entry so other characters notice it when they next check this file.

---

## Pre-team documentation history

Everything below happened before `TEAM.md`'s six-character split existed — it's the
specification work that produced the `docs/` tree the six characters now build against.
Kept here rather than deleted, since it's real history, just not attributable to a character.

### [Spec maintenance] 2026-09-04 — Identifier fix and consistency audit

**Built/changed:**
- Corrected the `SIH26176` → `SIH26117` identifier across 306 files (see
  `docs/20_DECISION_LOG.md` DEC-018).
- Ran a repository-wide consistency audit: 0 broken links across 7,819 cross-references, 0
  absolute-claim/overclaim language found (DEC-019).

**Status:** Documentation identifier and internal link integrity confirmed clean. This pass's
conclusion that "no further rewriting was needed" was later found inaccurate — see the next
entry.

### [Spec maintenance] 2026-09-04 — Master-prompt compliance audit and remediation

**Built/changed:**
- Full 63-section compliance audit against the original master prompt
  (`docs/MASTER_PROMPT_COMPLIANCE_AUDIT.md`, `docs/DETAILED_FINDINGS_AND_REMEDIATION_PLAN.md`):
  16 complete, 27 partial, 12 missing, 4 contradictory.
- Remediated P0/P1 and most of P2/P3 (see `docs/20_DECISION_LOG.md` DEC-020 for the full list):
  rewrote `docs/05_ARCHITECTURAL_PRINCIPLES.md` and `docs/06_TECHNOLOGY_STACK.md` (were empty
  templates); fixed the confidence-score methodology
  (`docs/features/14_evidence_and_provenance/08_confidence.md`); added the asset/equipment
  domain model (`docs/domain/20_asset_model.md`), the asset-centric knowledge graph
  (`docs/industrial/13_asset_knowledge_graph.md`), and cross-document contradiction detection
  (`docs/industrial/14_knowledge_conflict_detection.md`); added the asset UI screen
  (`docs/ui/23_asset_view.md`); extended `Document`/`Evidence` with the knowledge-trust-model
  and temporal-validity fields; expanded report generation to its full 11-section structure;
  wrote the real sovereignty-attestation mechanism; named the Context Security Boundary
  explicitly; wrote the concrete export-check sequence and model-router selection logic;
  expanded the threat model and feature matrix.
- Deferred explicitly, not silently dropped (DEC-021): DLP, the ~300-file `features/*`
  boilerplate-to-canonical-reference restructuring, two demo scripts, the temporal
  retrieval-time query filter's wiring, the 4th risk tier, and two undecided technology
  choices (reverse proxy, cache/queue).

**Status:** `docs/` now specifies the industrial-differentiation layer that was previously
missing at the entity/knowledge-graph level, not just at the document-workflow level. Nothing
in `services/`/`apps/` exists yet — this was entirely a specification pass.

**Next:** This is where `TEAM.md`'s six characters pick up — building actual code against
this now-more-complete specification. See `docs/08_BUILD_PHASES.md` for phase ordering
(Phase 0 — Foundation — is the natural starting point for Character 1).

---

## Team build history

*(Entries from here on are added by whichever character is actively building — see "How to
use this file" above. Nothing has been built yet as of the creation of this changelog; the
next entry below should be the first character's first real build session.)*
