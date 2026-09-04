# Local Text-to-Speech (V2+)

> Not part of V1. Would give the agent a spoken-response option, paired with `05_local_speech.md`
> for a full voice interaction loop (`07_field_engineer_voice_workflows.md`).

## Why deferred

Same rationale as `05_local_speech.md` — no current requirement drives it, and it adds a new
model capability slot and hardware budget line without displacing anything more valuable in
the 14-day V1 window.

## What a future spec would need to define

- A `tts` `ModelCapability` slot and its own latency budget (would likely fall under a new
  `runtime/11_retry_policy.md` operation class, since TTS streaming has different chunking
  characteristics than text generation).
- Whether TTS output is cached/reused for repeated content (e.g. standard UI copy) vs.
  generated fresh per response — a cost/latency tradeoff to make explicitly, not by default.
