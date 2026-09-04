# Demo Environment

> Concrete environment setup for the reference demo, extending `01_demo_overview.md`'s
> hardware/network mode summary.

## Machine setup

- PROFILE-B hardware (`07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`), freshly booted before the
  demo to ensure no memory pressure from unrelated processes.
- `deployment/03_docker_compose.md` stack already running and warmed (models loaded,
  `/readyz` green) at least 10 minutes before the demo starts — cold-start latency is
  excluded from the timed portion (`REQ-PERF-001`).
- Physical network disconnected or firewalled per `architecture/17_air_gapped_architecture.md`'s
  procedure, confirmed via the Network Sovereignty Panel before starting.

## Browser/display setup

Workbench UI open in a browser window sized for projection/screen-share; the Network
Sovereignty Panel (`ui/13_network_panel.md`) visible in the top bar throughout, per its
"always ambient" design intent.

## Backup environment

A second, identically-configured machine or VM snapshot, ready to swap to per
`13_failure_demo.md` if the primary demo machine has a hardware issue on the day.
