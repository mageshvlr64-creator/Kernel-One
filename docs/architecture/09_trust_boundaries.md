# Trust Boundaries

> Where data/control crosses from one trust level to another, per `security/03_trust_model.md`.

## Boundaries

1. **Browser ↔ API** — the outermost boundary; all input here is untrusted until validated
   and authenticated.
2. **Retrieved document content ↔ Agent Kernel context** — content crosses into the model's
   context window but is marked as untrusted data, never instruction (`security/05_prompt_injection.md`).
3. **Model output ↔ Tool Gateway** — a model's proposed tool call crosses from "semi-trusted
   proposal" to "must be independently authorized" at this boundary.
4. **Task workspace ↔ Host filesystem** — the Filesystem Tool and Code Execution sandbox both
   sit exactly on this boundary; everything on the host side of it is inaccessible from the
   workspace side by construction.
5. **Deployment ↔ external network** — the outermost boundary in the other direction; per
   REQ-NET-001, nothing crosses it outward by default.

## Rule

Every threat in `security/02_threat_model.md` maps to at least one boundary above — a threat
that doesn't correspond to any crossing point here is either mis-scoped or reveals a boundary
this file is missing (in which case, add it here first).

## The Context Security Boundary (per `SIH26117_Documentation_Refactor_Master_Prompt.txt` §15)

Boundaries 1-3 above are individually necessary but not sufficient — treating them as
independent checks (e.g. "the API layer did RBAC, so we're covered") misses that context can
still leak across the full chain from identity to output even when each individual hop looks
correct in isolation. The Context Security Boundary names that full chain as one thing to
verify end-to-end, not just hop-by-hop:

```
Identity (features/19_identity_and_rbac/)
  → Permissions (reference/05_permission_matrix.md)
    → Allowed Documents (features/13_knowledge_fabric/12_permission_filtering.md — filtered
      at retrieval time, boundary 2 above)
      → Evidence (domain/13_evidence_model.md — inherits its source Document's classification)
        → Tools (features/05_tool_gateway/ — boundary 3 above)
          → Models (features/02_model_router/ — model trust level is itself a routing input)
            → Artifacts (domain/14_artifact_model.md — classification inherited, never lowered)
              → Exports (features/20_data_classification/11_export_restrictions.md)
```

A user who cannot read a Document must never have that Document's content reach any hop past
"Allowed Documents" — not as a citation, not paraphrased into an answer, not summarized into
an Artifact. This is checked as one invariant across the full chain
(`testing/19_rbac_testing.md`), not assumed to follow automatically from each hop's individual
correctness.
