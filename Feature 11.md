# Feature 11 — Network Sovereignty Monitor

## Purpose
Turns "nothing leaves this laptop" from a claim into something a judge can watch. Your source doc is explicit about this (Section 20-21): don't say "trust us" — show a live panel proving internet, external DNS, external HTTP, and cloud APIs are all blocked, while internal traffic (UI→API, API→Model, API→VectorDB, Agent→Sandbox) flows normally. This is the single feature that makes the "sovereign/air-gapped" pitch defensible under a skeptical judge's follow-up question.

## How to build

1. **Application-layer egress guard (does the real enforcement)** — wrap all outbound HTTP calls in your backend behind one shared client/session object (e.g. one `httpx.Client` or `requests.Session` instance imported everywhere, never raw `requests.get()` scattered around). Configure it (or a small wrapper function) to check the target host against an allowlist (`localhost`, `127.0.0.1`, your own service ports) before every request and raise/log-and-block anything else. This is what actually stops an accidental outbound call from code you or a library wrote — it is cheap to add on Day 1 and expensive to retrofit once every feature has its own ad-hoc network calls.
2. **OS/process-level enforcement (the credible backstop)** — on the demo machine, run the backend process under a restricted network namespace or firewall rule that blocks all outbound traffic except loopback and the ports your own services use (e.g. `iptables`/`nftables` DROP rules for OUTPUT to non-local addresses, or a Linux network namespace with no default route). If firejail is available (see `03_HARDWARE_CONSTRAINTS.md`), its `--net=none` mode for the sandbox process covers Feature 06's isolation and can double as part of this story. This layer matters because it's what makes the claim true even if a bug slips past the application-layer guard — be honest in the pitch about which layer is doing the real enforcement (see failure table).
3. **Monitor process** — a lightweight background task (asyncio loop, every 2-5 seconds) that attempts a few cheap, clearly-external probes (e.g. DNS resolution of a public hostname, a TCP connect attempt to a known external IP on port 443) *expecting them to fail*, and records pass/fail. Do not literally hit an unpredictable third-party site for this — pick a stable target (e.g. `1.1.1.1:443`) so the "BLOCKED" result is deterministic during rehearsal.
4. **Internal traffic checks** — separately, ping/health-check your own internal components (API, model runtime, vector DB, sandbox) so the "internal traffic: ✓" rows are backed by a real check, not just "assumed running."
5. **Sovereignty panel (UI)** — render the two-column status view from your source doc almost verbatim: a "blocked" list (Internet connectivity, External DNS, External HTTP, Cloud APIs) and an "internal, working" list (UI→API, API→Model, API→VectorDB, Agent→Sandbox, OCR→Model). Poll this from the monitor process over the same WebSocket used by the execution graph (Feature 02), or a lightweight separate one — don't build a second transport just for this.
6. **Log any blocked attempt** — if the egress guard (step 1) ever actually blocks a real outbound call during the demo (e.g. a library silently tried to phone home), that's a first-class audit event (Feature 10), not a silent drop. A demo where you can show "here's the one time a library tried to call out, and here's it being blocked and logged" is a stronger proof than a panel that's never had anything to block.

## Data/API contract

```json
// Monitor status, pushed periodically
{
  "timestamp": "...",
  "external": {
    "internet": "blocked",
    "external_dns": "blocked",
    "external_http": "blocked",
    "cloud_apis": "blocked"
  },
  "internal": {
    "ui_to_api": "ok",
    "api_to_model": "ok",
    "api_to_vector_db": "ok",
    "agent_to_sandbox": "ok"
  },
  "blocked_attempts_session_total": 0
}
```

## Failure conditions

| Failure | Cause | Mitigation |
|---|---|---|
| Panel shows "BLOCKED" for everything but a library is quietly phoning home anyway (e.g. a telemetry call in a pip package) | Application-layer guard doesn't wrap every outbound call path; some library bypasses your shared client | Prefer the OS/process-level firewall rule as the real backstop (step 2) — the application guard is a nice-to-have signal layer, not the enforcement of record; state this precisely in the pitch |
| Demo venue actually has flaky/no internet and the "BLOCKED" status is indistinguishable from "network is just down anyway" | Monitor only checks pass/fail, no distinction between "actively denied" vs "no route" | Fine for the demo either way (both prove nothing got out) but be ready to explain the difference if a judge asks — don't overclaim active denial if you only tested with the venue's Wi-Fi off |
| Sovereignty panel itself needs network to render (e.g. loads a CDN font/icon) | Frontend pulled an external asset instead of bundling everything locally | Vendor all frontend assets locally (see `02_STACK.md`'s no-CDN-dependency framing) — this is an easy, embarrassing thing to get caught on live |
| Monitor's own external-probe attempt looks like a real, unblocked outbound call in a packet capture a technical judge asks to see | Probe uses a real DNS/TCP attempt against a live target | Fine — the probe attempt is *supposed* to happen and fail; make sure the target port genuinely gets refused/timed-out at the firewall, not silently caught in application code before it reaches the OS layer, or the "proof" is circular |
| Panel is static/decorative (hardcoded "BLOCKED" strings) rather than backed by real checks | Built as a UI mock late, under time pressure, without wiring real probes | Treat this feature's Definition of Done as requiring a live, periodically-refreshed check — a hardcoded panel is worse than no panel if a judge asks you to unplug the ethernet cable and watch it change |

## Definition of Done
The sovereignty panel is visible throughout the full demo flow (Demo Script), shows real, periodically-refreshed pass/fail for both external-blocked and internal-working checks, and — if the egress guard or firewall ever blocks a real attempted outbound call during rehearsal or the live demo — that event is visible in the panel's running total and appears in the audit log.
