# Permission Matrix (Canonical)

> **Canonical owner** of every role, permission, and resource/action pairing in the system.
> Feature documents reference this file; they do not restate role tables locally.

## Roles

| Role | Description |
|---|---|
| `Administrator` | Full system access, including user/role management, policy configuration, and approval of high-risk actions. |
| `Security Officer` | Can approve high-risk/classification-sensitive actions and view all audit data; cannot manage users or system configuration. |
| `Operator` | Can manage models, deployments, and system health; cannot approve high-risk actions or manage users. |
| `Analyst` | Standard end user: creates tasks, uploads documents (up to their clearance), views evidence/artifacts they're entitled to. |
| `Restricted User` | Chat and document upload only; no code execution, no tool use beyond read-only retrieval, no artifact export. |
| `Auditor` | Read-only access to audit logs and system configuration history; cannot act on anything. |

## Resources and actions

Resources: `Task`, `ToolInvocation`, `Model`, `ModelDeployment`, `Document`, `Artifact`,
`Approval`, `AuditEvent`, `User`, `Role`, `Policy`, `SystemConfiguration`.

Actions: `create`, `read`, `update`, `delete`, `execute`, `approve`, `export`.

## Matrix

| Resource | Action | Administrator | Security Officer | Operator | Analyst | Restricted User | Auditor |
|---|---|---|---|---|---|---|---|
| Task | create | ✅ | ✅ | ✅ | ✅ | ✅ (chat/upload tasks only) | ❌ |
| Task | read (own) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Task | read (others', same workspace) | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| Task | delete | ✅ | ❌ | ❌ | ✅ (own) | ❌ | ❌ |
| ToolInvocation | execute (`risk=low`) | ✅ | ✅ | ✅ | ✅ | ✅ (read-only tools only) | ❌ |
| ToolInvocation | execute (`risk=medium`) | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| ToolInvocation | execute (`risk=high`) | ✅ (requires approval) | ❌ | ❌ | ❌ (requires approval, admin/SO approves) | ❌ | ❌ |
| Model | read | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Model | create/update (registry) | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| ModelDeployment | create/update/delete | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Document | create (upload) | ✅ | ✅ | ✅ | ✅ (up to own clearance) | ✅ (up to own clearance) | ❌ |
| Document | read | ✅ | ✅ (per classification) | ✅ (per classification) | ✅ (per classification) | ✅ (per classification) | ❌ |
| Document | delete | ✅ | ❌ | ❌ | ✅ (own, INTERNAL or below) | ❌ | ❌ |
| Artifact | create | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Artifact | export | ✅ (requires approval if classification ≥ CONFIDENTIAL) | ✅ | ❌ | ✅ (requires approval if classification ≥ CONFIDENTIAL) | ❌ | ❌ |
| Approval | approve/reject | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| AuditEvent | read | ✅ | ✅ | ✅ (own actions only) | ❌ | ❌ | ✅ |
| User | create/update/delete | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Role | assign | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Policy | create/update | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| SystemConfiguration | update | ✅ | ❌ | ✅ (deployment/model config only) | ❌ | ❌ | ❌ |

## Conditions layered on top of the role check

A role granting `✅` is necessary but not always sufficient. The **policy engine**
(`features/21_policy_engine/`) additionally evaluates, per request:

1. **Classification condition** — caller's clearance must be ≥ resource's classification
   (`features/20_data_classification/`).
2. **Workspace condition** — caller must belong to the resource's workspace, unless role is
   `Administrator`/`Auditor`.
3. **Approval condition** — if the resource/action pair is `risk=high`
   (`reference/03_risk_levels.md`), an `Approval` record with `decision=approved` must exist
   for this specific action before it executes, regardless of role.

## How feature documents use this file

A feature document's "Permission requirements" section states only: the resource, the action,
and any resource-specific condition beyond the three listed above — e.g. "Resource: `Document`,
Action: `delete`. See `reference/05_permission_matrix.md` for the role table; no
document-specific condition beyond classification and workspace." It does not repeat the
admin/operator/restricted table.
