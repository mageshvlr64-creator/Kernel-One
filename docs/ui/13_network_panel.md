# Network Sovereignty Panel

> Screen specification. Behavior here is authoritative for this screen; `ui/01_ui_architecture.md`
> and `ui/02_design_system.md` define the shared visual/interaction conventions this screen
> follows.

## Purpose

Live proof of zero external egress (REQ-NET-003)

## User roles

All roles (read-only)

## Key elements

Per `SIH26117_Documentation_Refactor_Master_Prompt.txt` §41's field vocabulary, shown as a
status summary above the detail lists below:

- **Mode** — Air-Gapped / Restricted / Connected On-Premise (`features/18_network_sovereignty/02_network_modes.md`)
- **Internet** — Blocked / Allowed (per active mode)
- **External AI calls** — Blocked / Allowed (should read Blocked in every V1 mode — see `05_ARCHITECTURAL_PRINCIPLES.md` principle 1)
- **Local models** — which models are currently loaded and serving (`integrations/02-04_*.md`)
- **Local knowledge** — document/index counts, confirming retrieval is served from local storage, not an external index
- **Network attestation** — PASSED / FAILED, driven by `features/18_network_sovereignty/12_sovereignty_status.md`'s attestation mechanism

Detail lists, unchanged from the original screen spec:

- Blocked-checks list (green/red)
- Internal-health-checks list
- Blocked-attempts counter

## Actions available

- Primary actions are gated by the same permission check as their underlying API call
  (`reference/05_permission_matrix.md`) — a control is either fully hidden or fully enabled,
  never shown-then-rejected-with-no-explanation.

## States

Empty: N/A (always shows current status). Loading: 'Connecting to network monitor...' on first load only. Error: 'Network monitor unreachable' shown as its own red status, distinct from a blocked-check pass — this is itself alarming and should be visually distinct. Permission-denied: N/A, always visible to build trust.

## Related

- `reference/05_permission_matrix.md` for exactly which role sees which control.
- `reference/01_error_codes.md` for the exact error messages shown in the Error state.
- The API endpoint(s) this screen calls, under `docs/api/`.
