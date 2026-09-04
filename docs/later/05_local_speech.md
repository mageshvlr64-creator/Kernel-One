# Local Speech-to-Text (V2+)

> Not part of V1. Adding voice input would extend `05_chat_api.md` with an audio-upload
> variant and a local ASR (Automatic Speech Recognition) pipeline component.

## Why deferred

V1's demo and target workflows (`demo/01_demo_overview.md`) are text/document-centric; voice
input adds a new modality with its own accuracy, latency, and hardware-profile implications
(a local ASR model competes for the same VRAM budget documented in
`07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`) without being required by any current REQ-* entry.

## What a future spec would need to define

- A new `ModelCapability` slot (`asr`) with its own hardware-fit rules (`domain/08_model_provider_model.md`).
- Whether transcription happens client-side (before upload) or server-side — this has
  sovereignty implications (a client-side ASR library must still meet REQ-NET-001, i.e. no
  cloud ASR API calls from the browser) worth an explicit `DECISION REQUIRED` entry when this
  work is scheduled.
- Error handling for transcription confidence, mirroring the OCR confidence pattern already
  established in `industrial/02_inspection_reports.md`.
