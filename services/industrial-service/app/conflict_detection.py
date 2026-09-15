"""
Knowledge conflict detection for the industrial intelligence layer.

Implements the detection flow defined in:
  docs/industrial/14_knowledge_conflict_detection.md

KEY INVARIANT (principle 12, docs/05_ARCHITECTURAL_PRINCIPLES.md):
  This module NEVER auto-resolves a conflict.  If two currently-effective,
  equally-authoritative documents disagree about the same parameter, the
  conflict is surfaced as-is and flagged as "unresolved — requires human review."
  Picking one silently would violate principle 12.

What this module does NOT do:
  - It does not proactively scan the entire document corpus (V1 scope note
    in docs/industrial/14_knowledge_conflict_detection.md).
  - It does not fetch Evidence rows itself — callers pass pre-fetched evidence
    claim lists (same retrieval-before-generation pattern as comparison.py).
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any, Optional

from app.comparison import _normalize_parameter
from app.database import KnowledgeGraphRepository
from app.models import ConflictRecord

# ---------------------------------------------------------------------------
# Authority rank — used to decide how to present conflicting claims
# (does NOT auto-resolve; see module docstring)
# ---------------------------------------------------------------------------

AUTHORITY_RANK: dict[str, int] = {
    "primary": 3,
    "secondary": 2,
    "reference": 1,
}

# The minimum score for both sources to be considered "equally authoritative"
# and therefore a genuine conflict rather than an obvious precedence case.
EQUALLY_AUTHORITATIVE_RANK = AUTHORITY_RANK["primary"]


def _dates_overlap(
    from_a: Optional[date],
    until_a: Optional[date],
    from_b: Optional[date],
    until_b: Optional[date],
) -> bool:
    """Return True if the two validity windows overlap.

    A document with no effective_until is still currently in force (open-ended).
    A document with no effective_from is assumed to have always been in force.

    Per docs/industrial/14_knowledge_conflict_detection.md step 4:
        "If the two sources' validity windows don't overlap ... this isn't a
         live conflict, it's ordinary history."
    """
    today = date.today()
    # Treat None effective_until as "open-ended" (still in force today)
    end_a = until_a if until_a is not None else today
    end_b = until_b if until_b is not None else today

    # Treat None effective_from as "always"
    start_a = from_a if from_a is not None else date.min
    start_b = from_b if from_b is not None else date.min

    return start_a <= end_b and start_b <= end_a


def detect_conflicts(
    equipment_id: uuid.UUID,
    claims: list[dict[str, Any]],
) -> list[ConflictRecord]:
    """Run the conflict-detection flow for one piece of equipment.

    Args:
        equipment_id:  The Equipment row being analysed.
        claims:        List of claim dicts, one per Evidence-backed claim
                       retrieved from documents governing this equipment.
                       Each dict must contain:
                         - "document_id"        (UUID)
                         - "document_name"      (str)
                         - "authority"          (str, e.g. "primary")
                         - "effective_from"     (date | None)
                         - "effective_until"    (date | None)
                         - "parameter"          (str) — normalized parameter name
                         - "value"              (str) — the asserted value/claim

    Returns:
        List of ConflictRecord objects (empty if no conflicts detected).
        Each record has status="unresolved" — resolution is a human action,
        not something this function performs.
    """
    conflicts: list[ConflictRecord] = []

    # Group claims by normalized parameter name
    by_parameter: dict[str, list[dict]] = {}
    for claim in claims:
        key = _normalize_parameter(claim.get("parameter", ""))
        by_parameter.setdefault(key, []).append(claim)

    for parameter, param_claims in by_parameter.items():
        # Only need to check when there are at least 2 sources for the same parameter
        if len(param_claims) < 2:
            continue

        for i in range(len(param_claims)):
            for j in range(i + 1, len(param_claims)):
                a = param_claims[i]
                b = param_claims[j]

                # Skip if same document (shouldn't happen, but guard anyway)
                if a["document_id"] == b["document_id"]:
                    continue

                # Skip if values agree
                if a.get("value") == b.get("value"):
                    continue

                # Step 4: check temporal overlap — non-overlapping windows are
                # ordinary history, not live conflicts
                if not _dates_overlap(
                    a.get("effective_from"),
                    a.get("effective_until"),
                    b.get("effective_from"),
                    b.get("effective_until"),
                ):
                    continue

                # Step 3 + 5: compare authority
                rank_a = AUTHORITY_RANK.get(a.get("authority", ""), 0)
                rank_b = AUTHORITY_RANK.get(b.get("authority", ""), 0)

                # If both are equally authoritative (both primary) → genuine conflict
                # If one is lower authority → surface but label accordingly
                # Either way: NEVER auto-resolve.
                is_genuine_conflict = (
                    rank_a == EQUALLY_AUTHORITATIVE_RANK
                    and rank_b == EQUALLY_AUTHORITATIVE_RANK
                )

                if not is_genuine_conflict and rank_a == rank_b:
                    # Same non-primary authority: still surface it
                    is_genuine_conflict = True

                conflicts.append(
                    ConflictRecord(
                        equipment_id=equipment_id,
                        claim_description=(
                            f"{parameter.title()} for Equipment (id={equipment_id})"
                        ),
                        source_a_document_id=uuid.UUID(str(a["document_id"])),
                        source_a_document_name=a.get("document_name", ""),
                        source_a_authority=a.get("authority", "unknown"),
                        source_a_effective_from=a.get("effective_from"),
                        source_a_effective_until=a.get("effective_until"),
                        source_a_claim=a.get("value", ""),
                        source_b_document_id=uuid.UUID(str(b["document_id"])),
                        source_b_document_name=b.get("document_name", ""),
                        source_b_authority=b.get("authority", "unknown"),
                        source_b_effective_from=b.get("effective_from"),
                        source_b_effective_until=b.get("effective_until"),
                        source_b_claim=b.get("value", ""),
                        status="unresolved",
                        resolution_note=None,
                    )
                )

    return conflicts


def _format_window(from_date: Optional[date], until_date: Optional[date]) -> str:
    """Render a validity window per the spec's output example.

    Open-ended (still in force) renders as "<from>–present"; a closed window
    renders the full range so history reads as history, not a live conflict.
    """
    start = from_date.isoformat() if from_date else "unknown date"
    end = until_date.isoformat() if until_date else "present"
    return f"{start}–{end}"


def format_conflict_output(conflict: ConflictRecord) -> str:
    """Render a ConflictRecord as the canonical CONFLICT DETECTED text block.

    Format per docs/industrial/14_knowledge_conflict_detection.md Output section.
    Used when the agent must present the conflict in a chat response — principle 12
    requires this wording rather than picking one source silently.
    """
    window_a = _format_window(
        conflict.source_a_effective_from, conflict.source_a_effective_until
    )
    window_b = _format_window(
        conflict.source_b_effective_from, conflict.source_b_effective_until
    )
    return (
        f"CONFLICT DETECTED\n"
        f"Claim: {conflict.claim_description}\n"
        f"Source A: {conflict.source_a_document_name} "
        f"(authority: {conflict.source_a_authority}, "
        f'effective {window_a}) — "{conflict.source_a_claim}"\n'
        f"Source B: {conflict.source_b_document_name} "
        f"(authority: {conflict.source_b_authority}, "
        f'effective {window_b}) — "{conflict.source_b_claim}"\n'
        f"Status: Unresolved — requires human review"
    )
    from_b = (
        conflict.source_b_effective_from.isoformat()
        if conflict.source_b_effective_from
        else "unknown date"
    )
    return (
        f"CONFLICT DETECTED\n"
        f"Claim: {conflict.claim_description}\n"
        f"Source A: {conflict.source_a_document_name} "
        f"(authority: {conflict.source_a_authority}, "
        f'effective {from_a}–present) — "{conflict.source_a_claim}"\n'
        f"Source B: {conflict.source_b_document_name} "
        f"(authority: {conflict.source_b_authority}, "
        f'effective {from_b}–present) — "{conflict.source_b_claim}"\n'
        f"Status: Unresolved — requires human review"
    )
