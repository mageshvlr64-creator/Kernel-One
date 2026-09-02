# AI Implementation Protocol

This document is the detailed version of `AGENTS.md`, for AI agents doing substantial,
multi-file implementation work against this specification.

## Step 1 — Orient

Read, in order: `00_README.md`, `01_PRODUCT_VISION.md`, `02_SCOPE_AND_NON_GOALS.md`,
`04_SYSTEM_ARCHITECTURE.md`, `13_DEVELOPER_RULES.md`. Do not skip this even if the task looks
small — a "small" change to a schema can ripple through five other files.

## Step 2 — Locate the relevant spec

Find the feature group(s) under `docs/features/` that own the behavior you're changing. Read
every one of the 30 sections in the relevant file(s), not just Purpose and Scope. Pay specific
attention to: Permission requirements, Failure modes, Audit requirements, Forbidden
implementations — these are the sections most likely to contain a constraint that isn't
obvious from the feature name alone.

## Step 3 — Check dependencies and build order

Consult `09_BUILD_ORDER.md` and `10_DEPENDENCY_GRAPH.md`. If the feature you're building
depends on something not yet implemented, either implement the dependency first or clearly
stub it with a `TODO` that references the missing feature's doc path — never fake a
dependency's behavior silently.

## Step 4 — Implement against the contract, not your assumptions

Use the exact field names, types, and error shapes given in the relevant `schemas/` and `api/`
files. If the spec is ambiguous, make the smallest reasonable choice, implement it, and log the
choice in `20_DECISION_LOG.md` — do not silently invent a contract that isn't written down
anywhere for the next agent or human to find.

## Step 5 — Wire in the cross-cutting concerns

Every new capability must, where applicable:

- Pass through RBAC/policy checks (`features/19_identity_and_rbac/`, `features/21_policy_engine/`)
- Emit audit events (`features/17_audit/`)
- Respect the active network mode (`features/18_network_sovereignty/`)
- Route risky actions through approval (`features/16_human_approval/`)
- Emit logs/metrics per `features/25_observability/`

Skipping any of these is not "finishing it later" — it is an incomplete implementation.

## Step 6 — Test against the spec's own acceptance criteria

Use the "Test requirements" and "Acceptance criteria" sections of the feature file as your
test plan, not just your own judgment of what's worth testing.

## Step 7 — Reconcile docs and code

If anything you implemented differs from what the doc said (because the doc was wrong, or
because you had to make a call), update the doc in the same change. Never leave a diff where
only the code changed and the doc still describes the old behavior.

## Non-negotiables (repeated from AGENTS.md)

- No silent failure. No unaudited action. No unapproved high-risk action. No unsanctioned
  network egress. No scope creep into `later/`.
