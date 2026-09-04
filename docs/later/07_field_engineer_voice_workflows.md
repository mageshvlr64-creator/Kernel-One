# Field Engineer Voice Workflows (V2+)

> The combined use case `05_local_speech.md` + `06_local_tts.md` would enable: a field
> engineer using voice input/output hands-free while inspecting equipment, dictating findings
> that flow into the same `industrial/02_inspection_reports.md` pipeline as typed input.

## Why this is named as its own item rather than folded into speech/TTS

The workflow-level requirements (hands-free operation, noisy-environment ASR robustness,
possibly offline mobile/edge hardware distinct from `07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`'s
profiles) are a superset of "ASR + TTS exist" — this would likely need its own hardware
profile (call it PROFILE-E, a ruggedized edge device) and its own demo script, not just a
voice toggle on the existing workbench UI.

## Dependencies

Requires `05_local_speech.md` and `06_local_tts.md` to be built first, plus a new mobile/edge
client (distinct from the current React SPA, `ui/01_ui_architecture.md`) — this is a
substantial V2+ initiative, not an incremental feature.
