# Knowledge Conflict Detection and Resolution

> Per `SIH26117_Documentation_Refactor_Master_Prompt.txt` §9 and §39. Distinct from
> `industrial/06_change_detection.md`, which compares two *revisions of the same document
> lineage* (SOP-204 Rev.6 vs. Rev.7). This file covers two *independent, both-authoritative*
> documents that disagree — e.g. an SOP says a filter is replaced every 30 days, a Maintenance
> Manual for the same equipment says 45 days, and neither document is a revision of the other.

## Why this is a different problem from revision comparison

Revision comparison (§8) has a clear answer to "which version wins": the newer revision, by
definition. Conflict detection has no such built-in answer — both documents may currently be
in force, both may claim `authority = primary` (`domain/06_document_model.md`), and picking
one silently would violate `05_ARCHITECTURAL_PRINCIPLES.md` principle 12 ("never silently
resolve a knowledge conflict"). This is why conflict detection ends in a human decision, not
an automatic resolution, unlike revision comparison which can often auto-apply.

## When conflict detection runs

1. **At retrieval time**, when two or more Evidence rows backing the same answer come from
   different Document rows that are both `governed_by`-linked
   (`industrial/13_asset_knowledge_graph.md`) to the same Equipment, or otherwise both
   retrieved as relevant to the same query.
2. **As a standing background check**, when a new or updated Document is ingested: check
   whether any existing Document sharing a `governed_by` edge to the same Equipment makes a
   conflicting claim about the same parameter (see matching heuristic below).

## Detection flow

1. **Identify candidate conflicting sources** — Documents linked to the same Equipment (or,
   absent an Equipment link, the same retrieved-topic cluster) via
   `industrial/13_asset_knowledge_graph.md`'s `governed_by` edges.
2. **Extract the specific claim from each source** — reuses the same parameter/location
   matching heuristic already defined in `industrial/05_document_comparison.md` (the "does
   this look like the same underlying item" logic), applied here to decide whether two
   documents are making a claim about the *same* parameter (e.g. "filter replacement
   interval") rather than two unrelated numbers that happen to both be integers.
3. **Compare `Document.authority`** (`domain/06_document_model.md`) — if one source is
   `primary` and the other is `secondary`/`reference`, the primary source's claim is presented
   as current, but the secondary source's differing claim is still surfaced, not discarded,
   since it may indicate the secondary document is stale and needs updating.
4. **Compare `effective_from`/`effective_until`** — if the two sources' validity windows don't
   overlap (one has already been superseded), this isn't a live conflict, it's ordinary
   history — no action needed beyond what revision comparison already handles.
5. **If both sources are equally authoritative and both currently effective** — this is a
   genuine, unresolved conflict. It is surfaced, never auto-resolved.

## Output — `CONFLICT DETECTED`

When step 5 is reached, the system produces a conflict record (not a new entity table — a
structured `Evidence.verification_status = contradicted` pair, per `domain/13_evidence_model.md`)
shown to the user as:

```
CONFLICT DETECTED
Claim: Filter replacement interval for Equipment P-204
Source A: SOP-204 Rev.7 (authority: primary, effective 2024-03-01–present) — "30 days"
Source B: Maintenance Manual MM-118 (authority: primary, effective 2022-01-01–present) — "45 days"
Status: Unresolved — requires human review
```

The answer the agent gives in this situation states both values and the conflict explicitly —
it does not pick one, per `05_ARCHITECTURAL_PRINCIPLES.md` principle 12.

## Resolution flow

A human with `Document:reclassify` permission (the same role gate as changing
`Document.authority`, per `reference/05_permission_matrix.md`) resolves a conflict by one of:

- **Downgrading one source's authority** (e.g. marking the Maintenance Manual `secondary` if
  the SOP is confirmed as the actual governing document) — an audited action, per principle 9.
- **Setting `effective_until`** on the outdated source, if the conflict is actually a missed
  supersession that should have been recorded.
- **Explicitly acknowledging both as valid** (e.g. different intervals genuinely apply to
  different operating conditions) — recorded as a resolution note attached to the conflict,
  so future queries show the acknowledgment rather than re-flagging the same conflict.

Every resolution is an audited event (`features/17_audit/`) with the resolving user, the
chosen resolution, and a timestamp — the conflict's resolution becomes part of the system's
own auditable history, consistent with principle 9.

## Relationship to the verification pipeline

This feature is the "contradiction" check referenced by
`features/14_evidence_and_provenance/09_unsupported_claim_detection.md`'s broader verification
pipeline (`SIH26117_Documentation_Refactor_Master_Prompt.txt` §11) — when that pipeline's
contradiction-check step runs, it calls into this file's detection flow rather than
duplicating the logic.

## V1 scope note

Conflict detection in V1 requires both sources to already be linked to the same Equipment via
`governed_by` (or otherwise co-retrieved for the same query) — it does not proactively scan
the entire document corpus for conflicts unprompted. Corpus-wide proactive conflict scanning
is a reasonable V1.5/V2 extension, not attempted here, to keep the V1 scope bounded to what's
demonstrable: a conflict surfaces when it's relevant to a query or a new/updated ingestion
touches an already-linked Equipment, not as a standing full-corpus job.
