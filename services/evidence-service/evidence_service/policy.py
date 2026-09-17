"""Policy stub — mirrors docs/reference/05_permission_matrix.md (canonical, read-only).

Same canonical matrix implementation the sibling services use (documented in
DEC-023/DEC-024): role rows for the Document resource plus the layered conditions
(classification, workspace), with the decision bookkeeping the policy engine
(features/21) will take over. Authentication is a dev bearer-token stub (DEC-023)
until identity-service (Character 5) replaces it — the role always comes from the
server-side actor record, never a client field (feature docs §28).

Evidence feature docs §16: Resource `Document`, action `execute`, risk low —
Administrator / Security Officer / Operator / Analyst granted; Restricted User and
Auditor denied (TOOL_NOT_ALLOWED). Clearance ordering per
docs/features/20_data_classification/: PUBLIC < INTERNAL < CONFIDENTIAL < RESTRICTED.
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
    ("Document", "delete"): frozenset({ADMINISTRATOR, ANALYST}),
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

    if actor.role not in matrix:
        # TOOL_NOT_ALLOWED per registry: "Caller's role/policy does not permit this".
        # Role denial short-circuits before the classification layer (DEC-025 item 4).
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

    return PolicyDecision(True, "POLICY_ALLOWED", "granted by permission matrix")


def enforce(resource: str, action: str, actor: Actor, **kwargs) -> PolicyDecision:
    """check() + raise on denial. Always audit-log the denial at the call site."""
    decision = check(resource, action, actor, **kwargs)
    if not decision.allowed:
        raise RegistryError(decision.code, operator_detail=decision.rule)
    return decision
