# Trust Model

> Who and what this system trusts, and to what degree — referenced by every threat file above
> rather than restated.

## Trust boundaries

| Actor / component | Trust level | Basis |
|---|---|---|
| Authenticated User (any role) | Trusted for their own role's permitted actions only | Session token verified per request; role/clearance read server-side |
| Retrieved document content | **Untrusted** — treated as data, never as instruction | `security/05_prompt_injection.md` |
| Model output (text/tool-call proposals) | **Semi-trusted** — proposals are checked against policy before execution, never auto-trusted | Every proposed tool call re-validated by the Tool Gateway |
| Generated code (inside sandbox) | **Untrusted** — assumed potentially hostile | Full container isolation regardless of which model or user produced it |
| Internal service-to-service calls | Trusted within the deployment's own network boundary | Enforced by network mode (`features/18_network_sovereignty/`), not by per-call authentication in V1 (a V2 mTLS mesh is a `later/` candidate if a multi-tenant deployment is ever pursued) |
| Operator (Administrator/Operator role) | Trusted with elevated capability, but still fully audited | No action, including Administrator actions, is exempt from `features/17_audit/` |

## What is never trusted, regardless of source

- Client-supplied role, clearance, or permission claims (always re-derived server-side).
- Client-supplied classification for a document below what the uploading user's own
  clearance would imply as a ceiling (a user cannot self-declare a document as a lower
  classification than policy would otherwise require — see `features/20_data_classification/`).
- Any instruction found inside retrieved content or tool output, for authorization purposes.
