# Security Invariants

> The properties that must hold true at all times, regardless of feature, deployment mode, or
> code path. These are the "never" statements every other security document assumes.

1. **No outbound network call bypasses the active network mode's enforcement** (REQ-NET-001,
   REQ-NET-002) — verified continuously via `features/18_network_sovereignty/`, not just at
   deploy time.
2. **No state-changing action executes without a server-side authorization check**
   (REQ-SEC-001) — the Policy Engine fails closed if unreachable.
3. **No audit event is ever updated or deleted by application code** (REQ-SEC-005) — enforced
   at the database privilege level, not merely by application discipline.
4. **No code execution occurs outside the sandbox** (REQ-SEC-002), regardless of who or what
   requested it (user, agent, or an internal service acting on their behalf).
5. **No claim in agent output lacks a resolvable Evidence record** (REQ-FUNC-005) — enforced
   by `features/14_evidence_and_provenance/09_unsupported_claim_detection.md`, not just style
   guidance.
6. **No classification is silently lowered** — a derived entity's classification is always
   at least the maximum of its sources (REQ-DATA-001).
7. **No secret value appears in a log, error response, or non-Administrator config view**
   (`security/13_secret_exposure.md`).
8. **No approval is reusable after its gated action changes** — editing a pending high-risk
   action invalidates its Approval record (re-approval rule,
   `runtime/_state_machines_canonical.md#approval`).

## Verification

Each invariant above maps to at least one `SEC-TEST-###` or `TEST-*` case in
`testing/21_security_testing.md` or the relevant feature's own test requirements — an
invariant with no corresponding automated test is a gap to close before `08_BUILD_PHASES.md`
Phase 8 is considered complete, not an acceptable permanent state.
