# Vision-Language Model Failures

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

The vision-capable model fails to load, times out, or its response doesn't address the image (e.g. hallucinated content unrelated to what's shown).

## Detection

Same as `07_model_failures.md`/`08_model_timeout.md` plus a qualitative check: features/12_multimodal/09_multimodal_failures.md requires the model to state uncertainty rather than fabricate detail.

## System response

`MODEL_UNAVAILABLE`/`INFERENCE_TIMEOUT` for infra failures; for hallucination risk, the required caveat pattern (features/12_multimodal/06_photo_analysis.md) is a mitigation, not an automatic failure detector — V1 does not auto-detect hallucinated visual claims.

## Error code

`MODEL_UNAVAILABLE / INFERENCE_TIMEOUT` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Same fallback routing as text models; hallucination risk is disclosed to the user via UI copy, not silently corrected.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
