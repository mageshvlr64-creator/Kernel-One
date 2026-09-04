# UI Architecture

> Canonical structural overview. Individual screen files (`05_workbench_screen.md` onward)
> implement this structure; they do not redefine it.

## Stack

React SPA (`06_TECHNOLOGY_STACK.md`), served as static assets by the API layer's reverse
proxy in `air_gapped`/`on_premise` deployments — no CDN dependency (every asset, font, and
icon bundled locally, since a CDN fetch would itself violate REQ-NET-001).

## Layering

```
Screens (ui/05_..16_*.md)          -- one file per routed view
  └─ Panels (evidence, artifact, approval, network, security, model)
       └─ Shared components (design system, 02_design_system.md)
            └─ API client layer -- one function per docs/api/ endpoint, no ad hoc fetch() calls
```

## State management

- Server state (Tasks, Documents, Models, Approvals, etc.) is never duplicated into client-side
  global state beyond a short-lived cache — the UI always re-fetches or subscribes rather than
  trusting a stale local copy for anything permission- or state-machine-relevant.
- Real-time updates (Task state, Plan step status, Network Panel) use the streaming endpoint
  defined in `api/07_execution_api.md` / `api/22_network_api.md`, not polling, except where a
  file explicitly says otherwise (e.g. Network Panel polls at ≤5s per REQ-NET-003 as a
  documented exception since it's simpler and meets the latency bar).

## Permission-aware rendering

The UI calls `POST /api/v1/rbac/check` (`api/21_rbac_api.md`) to decide whether to render a
control at all — but the corresponding server-side check on the actual action endpoint is
always the authoritative gate (`reference/05_permission_matrix.md`). The UI check is a
convenience to avoid showing controls that will predictably fail, never a security boundary.

## Routing

One route per screen file under `ui/05_..16_*.md`; route guards redirect to `20_permission_denied_states.md`'s
403 page rather than rendering a broken/partial screen when the RBAC check fails.
