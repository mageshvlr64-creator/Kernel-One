from app.sop import evaluate_sop_compliance

GOOD_DISCLAIMER = (
    "Based on the text of the SOP document provided, "
    "not an independent regulatory assessment, the action matches Step 3."
)


def test_accepted_when_complete():
    ev = evaluate_sop_compliance(
        action_evidence_ids=["ev-1"],
        sop_evidence_ids=["ev-2"],
        agent_verdict="match",
        answer_text=GOOD_DISCLAIMER,
    )
    assert ev.accepted and ev.reasons == []


def test_rejects_missing_sop_side():
    ev = evaluate_sop_compliance(
        action_evidence_ids=["ev-1"],
        sop_evidence_ids=[],
        agent_verdict="match",
        answer_text=GOOD_DISCLAIMER,
    )
    assert not ev.accepted
    assert any("SOP side" in r for r in ev.reasons)


def test_rejects_missing_disclaimer():
    ev = evaluate_sop_compliance(
        action_evidence_ids=["ev-1"],
        sop_evidence_ids=["ev-2"],
        agent_verdict="match",
        answer_text="The action matches Step 3. Fully compliant.",
    )
    assert not ev.accepted
    assert any("disclaimer" in r for r in ev.reasons)


def test_rejects_bad_verdict():
    ev = evaluate_sop_compliance(
        action_evidence_ids=["ev-1"],
        sop_evidence_ids=["ev-2"],
        agent_verdict="probably fine",
        answer_text=GOOD_DISCLAIMER,
    )
    assert not ev.accepted
