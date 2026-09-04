# Log Management

> Concrete log handling procedure. Distinct from `features/17_audit/` (the tamper-evident
> business-event trail) — this covers application/infrastructure logs (stdout/stderr,
> structured debug/info/warn/error lines per `features/25_observability/02_structured_logging.md`).

## Retention

| Log type | Retention | Storage |
|---|---|---|
| Application structured logs | 30 days (CONFIG DEFAULT) | Local disk, rotated daily, gzip after 1 day |
| Audit events (`audit_events` table) | Indefinite — never auto-deleted | PostgreSQL, append-only |
| Sandbox execution logs (stdout/stderr per `ToolInvocation`) | 7 days (CONFIG DEFAULT) | Object storage, keyed by `tool_invocation_id` |

## Rotation procedure

1. Application logs rotate daily via the container runtime's logging driver (`json-file` with
   `max-size=100m, max-file=30`, or equivalent for the chosen orchestrator).
2. A nightly job compresses logs older than 1 day and deletes logs older than the retention
   window above — this job itself is auditable (`operations/08_backup_operations.md`-adjacent
   job logging).

## What must never appear in application logs

- Raw `password_hash`, `JWT_SIGNING_KEY`, or any value marked `Secret? yes` in
  `16_ENVIRONMENT_AND_CONFIGURATION.md`.
- Full document content — logs may reference a `document_id`, never the extracted text.
- Full tool-call payloads for `risk=high` tools — logs reference the `tool_invocation_id`;
  the actual payload lives only in the database, access-controlled the same as any other
  resource.

## Integrity check

A separate scheduled job re-walks the `audit_events` hash chain (REQ-SEC-005) weekly and
alerts if any link fails to verify — this is distinct from ordinary log rotation and is never
skipped even under storage pressure.
