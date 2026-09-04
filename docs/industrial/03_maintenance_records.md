# Maintenance Records

> Extends the inspection-report pattern (`02_inspection_reports.md`) to maintenance logs —
> structured or semi-structured records of work performed, parts replaced, and dates.

## Domain-specific expectation

A maintenance-record query (e.g. "when was this valve last serviced, and by what procedure")
should resolve to a specific record with a date and, where available, a technician/work-order
identifier — the agent does not summarize "maintenance has occurred periodically" when a
specific record answers the question directly; vague summarization when a precise citation is
available is treated as a quality defect, not an acceptable fallback.

## Cross-referencing with SOP compliance

`04_sop_compliance.md` builds on this: checking whether a maintenance record's actions match
the required procedure for that equipment class — this is a comparison between two document
types (maintenance record + SOP document), each independently retrieved and evidenced.
