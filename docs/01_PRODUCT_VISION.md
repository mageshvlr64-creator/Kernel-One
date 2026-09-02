# Product Vision

## The problem

Organizations that most need AI-assisted document reasoning, coding help, and report
generation — defense, critical infrastructure, regulated industry, government — are often the
organizations least able to send their data to a cloud LLM provider. Existing "enterprise AI"
offerings solve this by asking for trust in a vendor's data-handling promises. The
Sovereign AI Workbench solves it structurally: the model, the data, and the execution environment never
leave infrastructure the operator physically controls.

## The vision

A single workbench where a user can upload a pile of scanned inspection reports, ask a
question in plain language, and get back an answer with every claim traceable to a specific
page and coordinate in a specific source document — computed entirely by local models running
on hardware in the same building, with every step logged for audit, every risky action gated
on human approval, and a live panel proving nothing left the building while it happened.

## Who this is for

- An engineer who needs an inspection report summarized against a maintenance history, with
  citations a safety auditor will actually accept.
- A developer who wants an autonomous coding agent that can run and test code without handing
  proprietary source to a third party.
- A compliance or security team that needs to be able to prove, not just claim, that a
  deployment is sovereign.

## Why local models, not "just use a bigger cloud model"

Cloud convenience trades away exactly the property this product exists to provide. See
`06_TECHNOLOGY_STACK.md` for the specific model/runtime choices and `07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`
for what hardware makes this practical.

## Success looks like

- A user trusts an agent-generated report enough to act on it, because every claim in it is
  backed by a citation they can click through to the source.
- A security reviewer can watch the network sovereignty panel for the length of a full session
  and see zero unexplained external traffic.
- An operator can run this on a single workstation-class machine with no GPU cluster and no
  managed cloud service.

See `02_SCOPE_AND_NON_GOALS.md` for what is explicitly *not* part of this vision for V1.
