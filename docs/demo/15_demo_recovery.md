# Demo Recovery (Post-Demo)

> What happens after the demo ends, distinct from `13_failure_demo.md`'s during-demo recovery.

## Cleanup

1. Export the demo session's audit log (`api/19_audit_api.md`) if the audience/jury wants to
   review it afterward.
2. Reset the demo workspace (delete demo tasks/documents, or snapshot-restore to a clean
   pre-demo state) before the next rehearsal or live run, so `03_demo_data.md`'s deterministic
   findings aren't confused by leftover state from a prior run.
3. Note any deviation from the script (`05..12_*_demo.md`) that occurred, feeding back into
   `13_failure_demo.md`'s fallback list if it reveals a new failure mode worth preparing for
   next time.
