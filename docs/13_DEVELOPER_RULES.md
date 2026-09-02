# Developer Rules

These rules are non-negotiable for anyone — human or AI agent — contributing to the
Sovereign AI Workbench. They exist to keep ~650 documentation files and a growing codebase from drifting
apart.

## 1. Documentation standard for `features/`

Every file under `docs/features/<group>/` must contain, in order, all 30 sections defined in
the feature documentation template: Purpose, Scope, Non-goals, User-facing behavior, System
behavior, Inputs, Outputs, Preconditions, Postconditions, Data structures, API contracts,
Internal interfaces, State transitions, Dependencies, Security requirements, Permission
requirements, Failure modes, Retry behavior, Timeout behavior, Recovery behavior,
Observability requirements, Audit requirements, Performance requirements, Test requirements,
Acceptance criteria, Definition of done, Implementation notes, Forbidden implementations,
Examples, Edge cases. A section may be a single sentence if that's genuinely all there is to
say, but it must be present.

## 2. Docs and code must not drift

If you change behavior, you update the doc in the same change. If you find a doc that no
longer matches the code, you fix the mismatch before adding new behavior on top of it.

## 3. One source of truth per concern

A schema is defined once, in `docs/schemas/`. An API contract is defined once, in `docs/api/`.
A permission rule is defined once, in `docs/features/19_identity_and_rbac/` and enforced
through `docs/features/21_policy_engine/`. Nothing duplicates these definitions inline.

## 4. Every action is auditable

No feature is complete until its invocations produce an audit event per
`docs/features/17_audit/`. "We'll add logging later" is not an acceptable state to merge.

## 5. Every risky action is gated

If a feature's action is classified medium or high risk under
`docs/features/16_human_approval/02_action_risk_classification.md`, it must go through the
approval flow before executing — no exceptions for "just this once" or "the demo needs it to
be fast."

## 6. Nothing calls out

No code path may make an outbound network call that isn't explicitly permitted by the current
deployment's network mode (`docs/features/18_network_sovereignty/`). If you're not sure
whether a library does this, assume it might and check.

## 7. Fail loud, not silent

Every failure must map to a named entry in `docs/failures/`. Catching an exception and
returning a generic success, or swallowing it and logging nothing, is always wrong.

## 8. Scope discipline

If a capability lives under `docs/later/`, it is out of scope. Do not "just quickly" build
part of it because it seemed easy — it will create an inconsistent half-feature that's worse
than not having it.

## 9. Decisions get recorded

Any non-obvious design choice made while implementing a doc gets a one-paragraph entry in
`docs/20_DECISION_LOG.md`, dated, with the alternative(s) considered.

## 10. Consistency over speed

When a shortcut would violate rules 1-9 to hit a deadline, the shortcut is the wrong call.
Flag the conflict instead of silently taking it.
