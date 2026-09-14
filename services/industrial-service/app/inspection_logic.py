"""
Inspection report domain-specific logic.

Implements the domain expectations from docs/industrial/02_inspection_reports.md.

This module does NOT perform OCR or chunking — those belong to Character 3's
services/document-pipeline/ and services/knowledge-fabric/.  It provides
the domain-specific validation rules that Character 4 owns: what constitutes
a "finding" in this domain, what OCR confidence threshold triggers a warning,
and how to classify a finding vs. an unsupported claim.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# Configuration default per docs/industrial/02_inspection_reports.md
# "If OCR confidence ... below 0.85 (CONFIG DEFAULT)"
OCR_CONFIDENCE_WARN_THRESHOLD: float = 0.85


@dataclass
class Finding:
    """A structured inspection finding.

    A finding has the shape:
        {parameter, measured_value, specification, pass_fail, location_reference}

    Per docs/industrial/02_inspection_reports.md:
        "The agent MUST attach an Evidence record ... to every one of these four
         elements it states, not just the overall claim."

    All four required Evidence fields are tracked here so callers can validate
    completeness before accepting a finding as supported.
    """

    parameter: str
    measured_value: Optional[str]
    specification: Optional[str]  # threshold / spec limit
    pass_fail: Optional[str]      # e.g. "PASS", "FAIL", "15% below spec"
    location_reference: Optional[str]  # e.g. "Flange B, page 4"

    # Evidence IDs — one per element (not just the overall claim)
    evidence_id_parameter: Optional[str] = None
    evidence_id_measured_value: Optional[str] = None
    evidence_id_specification: Optional[str] = None
    evidence_id_pass_fail: Optional[str] = None

    ocr_confidence: Optional[float] = None  # from schemas/08_chunk_schema.md


def is_supported_finding(finding: Finding) -> bool:
    """Return True only if the finding has Evidence for all four required elements.

    A finding citing only the pass/fail verdict without the underlying measured
    value and threshold is treated as an unsupported claim per:
    docs/industrial/02_inspection_reports.md and
    docs/features/14_evidence_and_provenance/09_unsupported_claim_detection.md
    """
    return all(
        [
            finding.evidence_id_parameter,
            finding.evidence_id_measured_value,
            finding.evidence_id_specification,
            finding.evidence_id_pass_fail,
        ]
    )


def needs_ocr_confidence_warning(finding: Finding) -> bool:
    """Return True if the finding's source page has low OCR confidence.

    When True, the answer MUST flag the specific number as
    "OCR confidence lower than usual — verify against the original document"
    rather than stating it with the same certainty as a high-confidence value.

    Per docs/industrial/02_inspection_reports.md confidence handling section.
    """
    if finding.ocr_confidence is None:
        return False
    return finding.ocr_confidence < OCR_CONFIDENCE_WARN_THRESHOLD


def format_finding_answer_fragment(finding: Finding) -> str:
    """Produce a human-readable fragment for inclusion in an agent answer.

    Applies the OCR confidence warning where required.
    The caller is responsible for appending the Evidence citations.
    """
    param = finding.parameter or "Unknown parameter"
    location = f" ({finding.location_reference})" if finding.location_reference else ""

    value = finding.measured_value or "—"
    spec = finding.specification or "—"
    verdict = finding.pass_fail or "—"

    if needs_ocr_confidence_warning(finding):
        value = (
            f"{value} ⚠ OCR confidence lower than usual — verify against the original document"
        )

    return (
        f"{param}{location}: measured {value} vs. spec {spec} → {verdict}"
    )


def validate_sop_compliance_disclaimer(answer_text: str) -> bool:
    """Check that an SOP-compliance-framed answer includes the required disclaimer.

    Per docs/industrial/04_sop_compliance.md:
        "based on the text of the SOP document provided, not an independent
         regulatory assessment" (or equivalent) is part of the Definition of Done.
    """
    required_phrases = [
        "based on the text of the sop",
        "not an independent regulatory assessment",
        "not a regulatory assessment",
        "not a compliance certification",
    ]
    lower = answer_text.lower()
    return any(phrase in lower for phrase in required_phrases)


def validate_calculation_framing(answer_text: str) -> bool:
    """Check that an engineering-calculation answer states its verification scope.

    Per docs/industrial/11_calculation_verification.md:
        "arithmetic verified; formula selection and input values require human
         confirmation" (or equivalent).
    """
    required_phrases = [
        "arithmetic verified",
        "formula selection",
        "require human confirmation",
        "input values require",
    ]
    lower = answer_text.lower()
    return any(phrase in lower for phrase in required_phrases)
