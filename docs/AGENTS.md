# AGENTS.md

Instructions for any AI coding agent (Claude Code, Cursor, Copilot Workspace, or similar)
operating on the **Sovereign AI Workbench** (SIH26176) repository.

## What this repository is

This is a specification-first repository. The `docs/` tree is the source of truth for what
the system must do. Code does not exist yet, or exists partially; your job is to make the
code match the docs, not the other way around. If code and docs disagree, the docs win unless
a human explicitly tells you otherwise in the conversation — in that case, update the doc in
the same change that updates the code, so they never drift apart.

## Before writing any code

1. Read `docs/00_README.md`, `docs/01_PRODUCT_VISION.md`, and `docs/02_SCOPE_AND_NON_GOALS.md`.
2. Read `docs/04_SYSTEM_ARCHITECTURE.md` and `docs/05_ARCHITECTURAL_PRINCIPLES.md`.
3. Read `docs/13_DEVELOPER_RULES.md` in full — it is short and non-negotiable.
4. Find the specific feature file(s) under `docs/features/<group>/` relevant to your task and
   read every one of the 30 sections, not just "Purpose."
5. Check `docs/10_DEPENDENCY_GRAPH.md` and `docs/09_BUILD_ORDER.md` — do not build a feature
   whose declared dependencies don't exist yet.

## While writing code

- Follow `docs/15_CODEBASE_TARGET_STRUCTURE.md` for where new files belong.
- Every schema you introduce must match (or update) the corresponding file in `docs/schemas/`.
- Every API route you add must match (or update) the corresponding file in `docs/api/`.
- Every permission check must go through the RBAC/policy layer described in
  `docs/features/19_identity_and_rbac/` and `docs/features/21_policy_engine/` — never inline
  a role check ad hoc.
- Every tool call, model call, approval, and artifact write must produce an audit event per
  `docs/features/17_audit/`.
- Never add an outbound network call that isn't explicitly permitted by the active network
  mode in `docs/features/18_network_sovereignty/`.
- If you hit a decision not covered by the docs, make the smallest reasonable choice, implement
  it, and append a one-paragraph entry to `docs/20_DECISION_LOG.md` explaining the choice —
  do not leave the decision undocumented.

## After writing code

- Check your change against `docs/11_DEFINITION_OF_DONE.md` and
  `docs/12_GLOBAL_ACCEPTANCE_CRITERIA.md`.
- Add or update tests per the "Test requirements" section of the feature file(s) you touched.
- If you changed behavior described in a doc, update that doc in the same change.

## Forbidden

- Do not silently swallow exceptions. Every failure must map to a named failure mode in
  `docs/failures/`.
- Do not bypass the sandbox (`docs/features/09_code_execution/`) to "just run this quickly."
- Do not hardcode credentials, tokens, or API keys — see `docs/16_ENVIRONMENT_AND_CONFIGURATION.md`.
- Do not remove or weaken a security or RBAC check to make a demo path work; fix the actual
  blocker instead.
- Do not treat any file under `docs/later/` as in-scope without an explicit human instruction.

## See also

`docs/14_AI_IMPLEMENTATION_PROTOCOL.md` for the detailed, step-by-step protocol this file
summarizes.
