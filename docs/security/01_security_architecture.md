# Security Architecture

> Canonical overview. Individual threat files (`05_prompt_injection.md` through
> `24_data_in_transit.md`) are the source of truth for their own threat; this file defines the
> shared defense-in-depth principle and the layer model all of them follow.

## Defense-in-depth layers

1. **Perimeter:** Authentication (`features/19_identity_and_rbac/02_authentication.md`),
   network mode enforcement (`features/18_network_sovereignty/`).
2. **Authorization:** Policy Engine evaluated on every state-changing/classification-sensitive
   call (`features/21_policy_engine/`, REQ-SEC-001) — never bypassed for convenience.
3. **Isolation:** Sandbox for code execution (`features/09_code_execution/`), workspace-scoped
   filesystem access (`features/06_filesystem_tool/`).
4. **Detection:** Append-only, hash-chained audit trail (`features/17_audit/`, REQ-SEC-005) —
   every layer above produces an audit event on both allow and deny.
5. **Response:** Incident procedures (`operations/10_incident_response.md`,
   `11_security_incidents.md`, `12_network_incidents.md`).

## Principle: fail closed

Every check in every layer above fails closed — if the Policy Engine is unreachable, the
default is deny, not allow (REQ-SEC-001). No feature document may specify a fail-open
exception to this rule.

## Principle: no security-by-obscurity

This entire specification, including exact enforcement mechanisms, is written down and
distributed to every AI implementation agent working on the codebase — security here rests on
correct enforcement, not on secrecy of design.

## Threat catalog

See the individual files in this directory for each named threat's description, occurrence
surface, mitigation, and traceability. `02_threat_model.md` provides the consolidated table.
