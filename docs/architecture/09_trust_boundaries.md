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
