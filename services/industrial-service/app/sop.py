"""
SOP compliance cross-check for maintenance records.

Spec: docs/industrial/03_maintenance_records.md ("Cross-referencing with SOP compliance"),
      docs/industrial/04_sop_compliance.md

Checking whether a maintenance record's actions match the required procedure is a
comparison between two document types (maintenance record + SOP document), each
independently retrieved and evidenced.

What this module does:
- Gates an SOP-compliance answer on its two Definition-of-Done requirements:
  1. dual-sided evidence (at least one Evidence citation from EACH side —
     the maintenance record AND the SOP step), and
  2. the required scope disclaimer ("based on the text of the SOP document
     provided, not an independent regulatory assessment").

What this module does NOT do:
- It never decides match vs. no-match itself. The match verdict comes from the
  calling agent (which read both sides); this module only validates that the
  verdict is presented with both sides evidenced and properly disclaimed.
  A keyword-overlap "matcher" here would be model judgment dressed as
  determinism — explicitly avoided.
- It never claims regulatory or legal compliance (04_sop_compliance.md).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.inspection_logic import validate_sop_compliance_disclaimer

VALID_VERDICTS = ("match", "no_match", "uncertain")


@dataclass
class SopComplianceEvaluation:
    accepted: bool
    reasons: list[str] = field(default_factory=list)


def evaluate_sop_compliance(
    action_evidence_ids: list[str],
    sop_evidence_ids: list[str],
    agent_verdict: str,
    answer_text: str,
) -> SopComplianceEvaluation:
    """Validate that an SOP-compliance answer meets its Definition of Done."""
    reasons: list[str] = []
    if not action_evidence_ids:
        reasons.append("no Evidence cited from the maintenance-record side")
    if not sop_evidence_ids:
        reasons.append("no Evidence cited from the SOP side")
    if agent_verdict not in VALID_VERDICTS:
        reasons.append(
            f"verdict must be one of {VALID_VERDICTS}, got {agent_verdict!r}"
        )
    if not validate_sop_compliance_disclaimer(answer_text):
        reasons.append("missing required SOP scope disclaimer")
    return SopComplianceEvaluation(accepted=not reasons, reasons=reasons)
