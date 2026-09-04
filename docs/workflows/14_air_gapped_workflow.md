# Air-Gapped Operation Workflow

> End-to-end workflow specification. References the specific features involved rather than
> restating their internal behavior.

## Requirements implemented

REQ-NET-001, REQ-NET-002

## Steps

1. Deployment configured with NETWORK_MODE=air_gapped
2. Model weights, embedding models, and OCR models pre-loaded onto the host before network is disconnected (no runtime download capability in this mode)
3. All workflows above (01-13) function identically; the only difference is that any code path attempting outbound access fails immediately with NETWORK_EGRESS_BLOCKED rather than reaching a real host

## Notes

See architecture/17_air_gapped_architecture.md and demo/01_demo_overview.md.
