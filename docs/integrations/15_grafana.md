# Grafana Integration

> Dashboarding layer on top of Prometheus (`14_prometheus.md`), used by
> `ui/16_admin_console_ui.md`'s system health summary and by operators directly for deeper
> investigation.

## Deployment

Runs on-premise alongside Prometheus; dashboards are provisioned as code (JSON dashboard
definitions committed to the repository under `infra/`) rather than manually configured
per-deployment, so dashboard drift doesn't accumulate across environments.

## Access control

Grafana's own access control mirrors `reference/05_permission_matrix.md` — Administrator and
Operator roles get dashboard access; other roles do not have direct Grafana access (they use
the in-app Admin Console's summarized health view instead, `ui/16_admin_console_ui.md`).
