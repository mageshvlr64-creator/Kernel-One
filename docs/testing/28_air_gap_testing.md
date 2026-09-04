# Air-Gap Testing

> The most sovereignty-critical test file — physically or logically disconnects the network
> and verifies full functionality, not just "no crash."

## Method

1. Physically disconnect (or firewall at the router level) the test host's network interface.
2. Run the full demo scenario (`demo/01_demo_overview.md`) end-to-end.
3. Confirm every feature that should work offline does — document upload, OCR, RAG, agent
   tasks, code execution, artifact generation, approvals — with zero degraded behavior beyond
   what's explicitly documented (e.g. `deployment/06_cpu_only_demo.md`'s accepted latency
   tradeoff, which is about hardware not network).
4. Confirm every feature that should be blocked in this mode is (there should be none in V1 —
   the whole point of REQ-NET-001 is that air-gapped operation is fully functional, not a
   degraded mode).

## Rule

If any feature silently fails or degrades specifically because of network unavailability
(distinct from the accepted CPU-hardware-driven slowdown in `06_cpu_only_demo.md`), this is a
sovereignty-architecture defect — REQ-NET-001 promises full functionality offline, not a
"mostly offline" experience.
