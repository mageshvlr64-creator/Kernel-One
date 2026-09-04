# SOP Compliance

> Checking a maintenance action or inspection finding against a Standard Operating Procedure
> document, both already ingested via `features/10_document_ingestion/`.

## What the agent can and cannot claim

The agent CAN state: "The maintenance record's described action matches/does not match Step 3
of SOP-1147, cited here [evidence A] and here [evidence B]." The agent CANNOT claim regulatory
or legal compliance in an absolute sense — SOP-document-text matching is not the same as
compliance certification, and the UI/output must not imply otherwise
(`security/`-adjacent concern: overclaiming automated assurance is a trust/liability risk,
not just an accuracy one).

## Required disclaimer pattern

Any SOP-compliance-framed answer includes a stated scope: "based on the text of the SOP
document provided, not an independent regulatory assessment" — this sentence (or an
equivalent) is part of the Definition of Done for this capability, not optional UI copy.
