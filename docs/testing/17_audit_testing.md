# Audit Testing

> Covers `features/17_audit/` — completeness and tamper-evidence.

## Required tests

- `TEST-AUDIT-001`: for a scripted sequence of 50 mixed operations, audit event count exactly
  equals mutation count (REQ-AUD-001).
- `TEST-AUDIT-002`: an attempt to `UPDATE`/`DELETE` an audit row using the application's own
  database credentials fails at the database privilege level (REQ-SEC-005).
- Hash chain: corrupting one event's `payload_hash` out-of-band causes the integrity job
  (`operations/05_log_management.md`) to detect and alert on the break.
