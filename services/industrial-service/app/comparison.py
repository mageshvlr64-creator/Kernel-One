"""
Document comparison and change detection.

Implements the structured diff algorithm defined in:
  docs/industrial/05_document_comparison.md — overall approach
  docs/industrial/06_change_detection.md   — matching heuristic

This module receives pre-retrieved findings (already fetched from the
knowledge-fabric by the agent kernel) and applies the deterministic
classification rules to produce a DocumentDiff.

NOTE: This module does NOT perform retrieval itself — it never calls the
knowledge fabric directly.  The agent kernel retrieves chunks from each
document independently (one retrieval pass per document, each with its own
permission filter applied — REQ-FUNC-004 is never bypassed by treating the
pair as a merged context).  The retrieved findings are passed here as
structured Python dicts; this module only classifies them.
"""

from __future__ import annotations

import uuid
from typing import Optional

from app.models import DiffEntry, DocumentDiff

# ---------------------------------------------------------------------------
# Synonym table
# Per docs/industrial/06_change_detection.md:
#   "treated as equivalent only if an explicit synonym mapping exists,
#    never inferred by the model at comparison time"
# ---------------------------------------------------------------------------

SYNONYM_MAP: dict[str, str] = {
    # Normalized form → canonical parameter name
    "torque": "tightening torque",
    "tightening force": "tightening torque",
    "tightening torque": "tightening torque",
    "bolt torque": "tightening torque",
    "pressure": "operating pressure",
    "operating pressure": "operating pressure",
    "temperature": "operating temperature",
    "operating temperature": "operating temperature",
    "vibration": "vibration level",
    "vibration level": "vibration level",
}

# Threshold below which a diff entry is flagged as low-confidence.
LOW_CONFIDENCE_THRESHOLD = 0.7

# Cap applied to table-derived values per docs/industrial/07_engineering_documents.md:
# "table-derived values [treated] as lower-confidence by default than
#  directly-stated prose values, pending explicit verification."
TABLE_CONFIDENCE_CAP = 0.6


def apply_table_confidence_default(
    confidence: float | None, source_kind: str | None
) -> float | None:
    """Cap confidence for table-derived extractions.

    A mis-parsed spec table silently produces wrong "spec" values downstream,
    so table-derived values start capped at TABLE_CONFIDENCE_CAP until
    explicitly verified (11_calculation_verification.md). Prose values and
    unknown kinds pass through unchanged.
    """
    if confidence is None or source_kind != "table":
        return confidence
    return min(confidence, TABLE_CONFIDENCE_CAP)


def _normalize_parameter(raw: str) -> str:
    """Return the canonical parameter name for *raw*.

    If no synonym mapping exists, the normalized (lowercased, stripped)
    form is returned unchanged — never inferred.
    """
    normalized = raw.strip().lower()
    return SYNONYM_MAP.get(normalized, normalized)


def _normalize_location(raw: Optional[str]) -> Optional[str]:
    if raw is None:
        return None
    return raw.strip().lower()


def _is_match(finding_a: dict, finding_b: dict) -> bool:
    """Two findings match iff they share the same normalized parameter name AND,
    if both carry a location_reference, the same normalized location.

    Per docs/industrial/06_change_detection.md:
        "Two findings match if they share the same normalized parameter name
         ... AND the same location reference if present in both."
    If neither finding has a location, location is not used as a disambiguator.
    """
    param_a = _normalize_parameter(finding_a.get("parameter", ""))
    param_b = _normalize_parameter(finding_b.get("parameter", ""))
    if param_a != param_b:
        return False

    loc_a = _normalize_location(finding_a.get("location_reference"))
    loc_b = _normalize_location(finding_b.get("location_reference"))

    # Both carry a location — must match
    if loc_a is not None and loc_b is not None:
        return loc_a == loc_b

    # One or both missing — parameter match alone is sufficient
    return True


def compare_findings(
    document_a_id: uuid.UUID,
    document_b_id: uuid.UUID,
    findings_a: list[dict],
    findings_b: list[dict],
) -> DocumentDiff:
    """Produce a structured diff of two sets of findings.

    Args:
        document_a_id:  UUID of the "before" document.
        document_b_id:  UUID of the "after" document.
        findings_a:     List of finding dicts from document A. Each dict should have:
                          - "parameter"         (str, required)
                          - "location_reference" (str, optional)
                          - "value"             (str, optional)
                          - "confidence"        (float, optional, 0–1)
                          - "evidence_id"       (UUID str, optional)
        findings_b:     Same structure, from document B.

    Returns:
        DocumentDiff with added, removed, changed lists.

    Rules (per docs/industrial/05_document_comparison.md):
        - "changed" if same parameter+location in both, different value or verdict
        - "added"   if present only in document B
        - "removed" if present only in document A
        - Ambiguous near-matches (no synonym mapping, but plausibly related)
          are classified as "added", never silently matched — a false match that
          hides a genuinely new finding is a worse failure mode than an extra
          "added" entry a human reviewer can dismiss.
    """
    diff = DocumentDiff(document_a_id=document_a_id, document_b_id=document_b_id)
    matched_b_indices: set[int] = set()

    for fa in findings_a:
        matched = False
        for i, fb in enumerate(findings_b):
            if i in matched_b_indices:
                continue
            if _is_match(fa, fb):
                matched_b_indices.add(i)
                matched = True
                value_a = fa.get("value")
                value_b = fb.get("value")
                if value_a != value_b:
                    # Changed finding
                    confidence = min(
                        fa.get("confidence", 1.0) or 1.0,
                        fb.get("confidence", 1.0) or 1.0,
                    )
                    for f in (fa, fb):
                        capped = apply_table_confidence_default(
                            confidence, f.get("source_kind")
                        )
                        confidence = capped if capped is not None else confidence
                    entry = DiffEntry(
                        change_type="changed",
                        parameter=_normalize_parameter(fa["parameter"]),
                        location_reference=fa.get("location_reference")
                        or fb.get("location_reference"),
                        value_in_document_a=value_a,
                        value_in_document_b=value_b,
                        confidence=confidence,
                        evidence_id_a=_parse_uuid(fa.get("evidence_id")),
                        evidence_id_b=_parse_uuid(fb.get("evidence_id")),
                    )
                    diff.changed.append(entry)
                # If values are identical, finding is unchanged — not included in diff
                break

        if not matched:
            # Present in A but not matched in B — "removed"
            confidence = fa.get("confidence", 1.0) or 1.0
            capped = apply_table_confidence_default(confidence, fa.get("source_kind"))
            confidence = capped if capped is not None else confidence
            diff.removed.append(
                DiffEntry(
                    change_type="removed",
                    parameter=_normalize_parameter(fa["parameter"]),
                    location_reference=fa.get("location_reference"),
                    value_in_document_a=fa.get("value"),
                    value_in_document_b=None,
                    confidence=confidence,
                    evidence_id_a=_parse_uuid(fa.get("evidence_id")),
                    evidence_id_b=None,
                )
            )

    # Remaining unmatched B findings are "added"
    for i, fb in enumerate(findings_b):
        if i not in matched_b_indices:
            confidence = fb.get("confidence", 1.0) or 1.0
            capped = apply_table_confidence_default(confidence, fb.get("source_kind"))
            confidence = capped if capped is not None else confidence
            diff.added.append(
                DiffEntry(
                    change_type="added",
                    parameter=_normalize_parameter(fb["parameter"]),
                    location_reference=fb.get("location_reference"),
                    value_in_document_a=None,
                    value_in_document_b=fb.get("value"),
                    confidence=confidence,
                    evidence_id_a=None,
                    evidence_id_b=_parse_uuid(fb.get("evidence_id")),
                )
            )

    return diff


def _parse_uuid(raw: Optional[str]) -> Optional[uuid.UUID]:
    if raw is None:
        return None
    try:
        return uuid.UUID(str(raw))
    except ValueError:
        return None


def is_low_confidence(entry: DiffEntry) -> bool:
    """True if a diff entry should be flagged in the UI as lower-confidence.

    Per docs/industrial/06_change_detection.md:
        "Each diff entry carries the confidence of its underlying retrieval ...
         a low-confidence match is flagged distinctly in the UI rather than
         presented with the same certainty as a high-confidence one."
    """
    return (entry.confidence is not None) and (
        entry.confidence < LOW_CONFIDENCE_THRESHOLD
    )
