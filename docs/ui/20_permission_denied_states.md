# Permission-Denied States

> Canonical 403 rendering. Referenced by `03_navigation.md`'s route guards and by any inline
> control gated per `reference/05_permission_matrix.md`.

## Full-page 403

Shown when a route's screen requires a role/permission the user lacks. Renders: a clear
statement of what's restricted (not a generic "Access Denied"), and a link back to the
Workbench — never a raw `POLICY_DENIED` JSON body.

## Inline control-level denial

A control the user's role can never use (e.g. Approval buttons for an Analyst) is **hidden
entirely**, not shown-disabled — showing a permanently-disabled control the user can never
activate is a worse experience than not showing it, and risks implying escalation is possible
via some other path.

A control the user's role *can sometimes* use but not right now (e.g. Export blocked pending
approval) **is shown, disabled, with an explanatory tooltip** (`ApprovalGate` component,
`02_design_system.md`) — this case is genuinely conditional, so hiding it would hide useful
information about what would unblock it.

## Distinction from classification denial

`FILE_CLASSIFICATION_DENIED` (a document exists but the caller's clearance is insufficient)
renders as the document simply not appearing in `15_knowledge_browser.md`'s list — not as a
403 page for a document the user doesn't know exists (avoids confirming existence of content
above their clearance).
