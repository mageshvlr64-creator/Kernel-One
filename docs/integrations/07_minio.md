# MinIO Integration

> S3-compatible object storage (DEC-003) for Documents and Artifacts.

## Contract

Adapter uses the S3 API surface (`PutObject`, `GetObject`, `HeadObject`, lifecycle policies)
— chosen specifically so a future migration to a different S3-compatible store, or to genuine
AWS S3 for a cloud-permitted deployment variant (not currently in scope, would need its own
`DECISION REQUIRED` entry), requires only a configuration change, not an adapter rewrite.

## Bucket layout

One bucket per Workspace (or a prefix-per-workspace scheme within a single bucket — an
implementation choice not yet fixed; whichever is chosen, workspace isolation at the storage
layer is enforced by the adapter, not left to convention).

## Health check

`HEAD` on a known bucket, per `deployment/13_health_checks.md`.
