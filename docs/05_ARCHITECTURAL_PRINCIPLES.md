# Architectural Principles

> Root specification document · `docs/05_ARCHITECTURAL_PRINCIPLES.md`
> Previous: `04_SYSTEM_ARCHITECTURE.md` · Next: `06_TECHNOLOGY_STACK.md`

## Purpose

Fifteen non-negotiable principles. Every other document in this tree — every file under
`features/`, `architecture/`, `api/`, `ui/`, and so on — is expected to be consistent with
these. If a reviewer finds a feature file that conflicts with a principle below, the feature
file is wrong, not this one, unless this document is explicitly revised (with a note in
`20_DECISION_LOG.md`). This file exists so these rules live once instead of being repeated in
680 places.

## The 15 principles

1. **Local-first.** No feature may assume internet access is available or required for core
   operation. Local inference (`integrations/02-04_*.md`) is the default execution path in
   every network mode, including air-gapped (`architecture/17_air_gapped_architecture.md`).

2. **Evidence before assertion.** An agent may not present a claim as fact without a
   retrievable source backing it. This is why `Evidence` is a first-class entity
   (`domain/13_evidence_model.md`) rather than something assembled ad hoc in a prompt.

3. **Retrieval before generation.** For any question answerable from the operator's own
   documents, the system retrieves relevant content before generating a response — it does
   not generate first and look things up to justify the answer afterward. Enforced by the
   agent kernel's plan step ordering (`features/04_agent_kernel/04_planning.md`).

4. **Verification after generation.** A generated answer is checked against its cited
   evidence before being shown as final — citation validity, evidence support, and
   unsupported-claim detection are a required pipeline stage, not an optional add-on
   (`features/14_evidence_and_provenance/09_unsupported_claim_detection.md`).

5. **Least privilege by default.** Every agent run, tool call, and document retrieval is
   scoped to exactly the permissions the acting user holds — never inherited, never assumed,
   never elevated implicitly (`features/19_identity_and_rbac/`, `13_knowledge_fabric/12_permission_filtering.md`).

6. **Human approval for high-risk actions.** Actions above the low-risk tier
   (`reference/03_risk_levels.md`) pause for explicit human approval before executing
   (`features/16_human_approval/`) — the system proposes, a person disposes, for anything
   consequential or hard to reverse.

7. **Retrieved content is untrusted data, not instructions.** Text pulled from a document,
   tool output, or any other non-operator source is treated as data to reason about, never as
   commands to obey — this is the core defense in `security/05_prompt_injection.md`, and it
   applies uniformly regardless of how plausible or well-formatted the injected text looks.

8. **Deterministic components for deterministic work.** Where a correct answer exists and is
   computable exactly (arithmetic, unit conversion, engineering formulas), a deterministic
   component computes it — the LLM's job is to identify inputs and interpret results, never to
   compute the number itself (`industrial/10-11_*.md`, `features/07_calculator_tool/05_deterministic_verification.md`).

9. **Audit every action.** No feature may act without a corresponding, append-only audit
   record (`features/17_audit/`, `domain/17_audit_event_model.md`) — this is enforced at the
   API layer per `04_SYSTEM_ARCHITECTURE.md`'s request path, not left to individual features
   to remember.

10. **Classification never decreases.** A derived artifact's classification is computed as the
    maximum of every input's classification, never lower, and never manually downgraded
    without an explicit, audited override (`domain/01_domain_model.md` cross-cutting rule #1,
    `features/20_data_classification/`).

11. **Fail closed.** When a permission, policy, or classification check cannot be completed —
    due to an error, a missing value, or a downstream service being unreachable — the default
    is to deny the action, not to proceed optimistically. This applies uniformly across RBAC,
    policy engine, and network-sovereignty checks.

12. **Never silently resolve a knowledge conflict.** When two sources disagree, the system
    surfaces the conflict for human resolution rather than picking one source and presenting
    it as settled (`industrial/14_knowledge_conflict_detection.md`) — an unresolved conflict is
    shown as unresolved, not smoothed over.

13. **Never expose context the requesting user isn't authorized to see.** Permission filtering
    applies at retrieval time, not only at ingestion time (`04_SYSTEM_ARCHITECTURE.md`'s data
    path) — a document a user can't read must never surface in their evidence, citations, or
    generated answers, even indirectly.

14. **Prefer explainable execution traces over hidden reasoning.** What the agent did — which
    documents it retrieved, which tools it called, what each step returned — is shown to the
    user in a structured, safe trace format; raw model reasoning is not surfaced as if it were
    an audit-grade explanation of what actually happened
    (`features/04_agent_kernel/16_execution_trace.md`).

15. **Sovereignty is a property of the whole system, not a checkbox.** No single feature
    "is" sovereign — network isolation, local inference, audit, and access control together
    make the system's behavior verifiable as sovereign, which is why sovereignty status is
    continuously attested (`features/18_network_sovereignty/12_sovereignty_status.md`) rather
    than asserted once at deployment time.

## Enforcement

Adherence to these 15 principles is part of `11_DEFINITION_OF_DONE.md` and
`12_GLOBAL_ACCEPTANCE_CRITERIA.md` — checked at review time, not assumed. A feature document
that cannot point to how it satisfies the relevant principles above should be treated as
incomplete, not as implicitly compliant.

## Related documents

- `docs/13_DEVELOPER_RULES.md` — how these principles translate into per-file writing rules.
- `docs/14_AI_IMPLEMENTATION_PROTOCOL.md` — how an AI implementer should apply them during
  code generation.
- `docs/18_DOCUMENTATION_INDEX.md`

## Maintenance

Changes to this file must be reflected in `docs/20_DECISION_LOG.md` with the date, the reason
for the change, and which downstream documents were checked for consistency afterward.
