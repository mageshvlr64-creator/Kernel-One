"""Policy stub — mirrors docs/reference/05_permission_matrix.md (canonical, read-only).

This stub implements the canonical matrix rows for the Document resource plus the layered
conditions (classification, workspace) from the same file, and the decision bookkeeping the
policy engine (features/21) will take over. It must be kept byte-for-byte consistent with
the canonical matrix; the schema (docs/schemas/07) constrains classification values.

Matrix rows (Document):
  create (upload): Administrator, Security Officer, Operator, Analyst*, RestrictedUser*
                   (* up to own clearance; Auditor denied)
  read:            all except Auditor (per classification)
  delete:          Administrator; Analyst own-only INTERNAL-or-below; others denied
  execute:         treated as medium-risk tooling: Administrator, Security Officer,
                   Operator, Analyst; RestrictedUser and Auditor denied

Roles use the canonical names; the API's 'restricted' test alias maps to Restricted User.
Clearance ordering per docs/features/20_data_classification/: PUBLIC < INTERNAL <
CONFIDENTIAL < RESTRICTED.

Authentication is a dev stub in this increment: the bearer token must equal a seeded dev
token and identifies the actor; JWT verification lands with identity-service (Character 5).
Documented as DEC-023; forbidden by feature docs §28 to trust role from a client field —
the role always comes from the server-side actor record.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from .errors import RegistryError

CLEARANCE_ORDER = {"PUBLIC": 0, "INTERNAL": 1, "CONFIDENTIAL": 2, "RESTRICTED": 3}

# Canonical role names from reference/05_permission_matrix.md
ADMINISTRATOR = "Administrator"
SECURITY_OFFICER = "Security Officer"
OPERATOR = "Operator"
ANALYST = "Analyst"
RESTRICTED_USER = "Restricted User"
AUDITOR = "Auditor"

ALL_ROLES = (ADMINISTRATOR, SECURITY_OFFICER, OPERATOR, ANALYST, RESTRICTED_USER, AUDITOR)

# (resource, action) -> roles granted by the canonical matrix
_DOCUMENT_MATRIX: Dict[Tuple[str, str], frozenset] = {
    ("Document", "create"): frozenset({ADMINISTRATOR, SECURITY_OFFICER, OPERATOR, ANALYST, RESTRICTED_USER}),
    ("Document", "read"): frozenset({ADMINISTRATOR, SECURITY_OFFICER, OPERATOR, ANALYST, RESTRICTED_USER}),
    ("Document", "delete"): frozenset({ADMINISTRATOR, ANALYST}),  # Analyst: own + INTERNAL-or-below
    ("Document", "execute"): frozenset({ADMINISTRATOR, SECURITY_OFFICER, OPERATOR, ANALYST}),
}


@dataclass(frozen=True)
class Actor:
    """Server-side actor record. Never constructed from client-supplied fields."""
    actor_id: str
    role: str
    clearance: str = "INTERNAL"
    workspace_id: str = ""


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    code: str            # which registry code applies when denied
    rule: str            # the specific denying rule, for the audit 'reason'


def check(resource: str, action: str, actor: Actor, *,
          resource_classification: str = "INTERNAL",
          resource_workspace_id: str = "",
          resource_owner_id: str = "") -> PolicyDecision:
    matrix = _DOCUMENT_MATRIX.get((resource, action))
    if matrix is None:
        return PolicyDecision(False, "POLICY_DENIED", f"no matrix row for {resource}:{action}")

    # Layered condition 0: role — denied roles are TOOL_NOT_ALLOWED regardless of
    # classification, so the denial reason is never misattributed to clearance.
    if actor.role not in matrix:
        # TOOL_NOT_ALLOWED per registry: "Caller's role/policy does not permit this"
        return PolicyDecision(False, "TOOL_NOT_ALLOWED",
                              f"role {actor.role!r} not granted {resource}:{action}")

    # Layered condition 1: classification — caller clearance >= resource classification.
    if CLEARANCE_ORDER[actor.clearance] < CLEARANCE_ORDER[resource_classification]:
        return PolicyDecision(False, "FILE_CLASSIFICATION_DENIED",
                              f"clearance {actor.clearance} below classification "
                              f"{resource_classification}")

    # Layered condition 2: workspace — caller must belong to the resource's workspace,
    # unless role is Administrator/Auditor (canonical carve-out).
    if resource_workspace_id and actor.role not in (ADMINISTRATOR, AUDITOR):
        if actor.workspace_id != resource_workspace_id:
            return PolicyDecision(False, "POLICY_DENIED",
                                  "actor not in resource's workspace")

    # Resource-specific condition for delete: Analyst owns the document and it is
    # INTERNAL or below (canonical matrix note).
    if action == "delete" and actor.role == ANALYST:
        if resource_owner_id and resource_owner_id != actor.actor_id:
            return PolicyDecision(False, "POLICY_DENIED", "not owner")
        if CLEARANCE_ORDER[resource_classification] > CLEARANCE_ORDER["INTERNAL"]:
            return PolicyDecision(False, "POLICY_DENIED",
                                  "Analyst may delete only INTERNAL or below")

    return PolicyDecision(True, "POLICY_ALLOWED", "granted by permission matrix")


def enforce(resource: str, action: str, actor: Actor, **kwargs) -> PolicyDecision:
    """check() + raise on denial. Always audit-log the denial at the call site."""
    decision = check(resource, action, actor, **kwargs)
    if not decision.allowed:
        raise RegistryError(decision.code, operator_detail=decision.rule)
    return decision


# ---------------------------------------------------------------------- dev auth stub

# Dev bearer tokens -> server-side actor records (DEC-023). identity-service replaces this
# with JWT session resolution; the contract is only that the Actor comes from the
# server side. Role is NEVER read from a client-supplied field (feature docs §28).
_DEV_TOKEN = "dev-token-{slug}"


def _dev_actor(slug: str, role: str, clearance: str, workspace_id: str = "dev-workspace") -> Actor:
    import uuid as _uuid
    return Actor(actor_id=str(_uuid.uuid5(_uuid.NAMESPACE_URL,
                                          f"dev-actor:{slug}")),
                 role=role, clearance=clearance, workspace_id=workspace_id)


DEV_ACTOR_TOKENS = {
    _DEV_TOKEN.format(slug=slug): _dev_actor(slug, role, clearance)
    for slug, role, clearance in (
        ("administrator", ADMINISTRATOR, "RESTRICTED"),
        ("security-officer", SECURITY_OFFICER, "RESTRICTED"),
        ("operator", OPERATOR, "CONFIDENTIAL"),
        ("analyst", ANALYST, "INTERNAL"),
        ("restricted", RESTRICTED_USER, "INTERNAL"),
        ("auditor", AUDITOR, "RESTRICTED"),
    )
}
