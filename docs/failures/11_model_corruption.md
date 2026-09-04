# Model Corruption

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

A model checkpoint fails its checksum verification at load time (security/22_supply_chain_security.md), or produces systematically degraded output.

## Detection

Checksum check at registration (features/01_model_management/05_model_installation.md); output-quality regression caught by benchmarking (later/11_advanced_model_benchmarking.md, V2) or manual report in V1.

## System response

Registration is refused (`MODEL_NOT_APPROVED`-adjacent failure) if checksum fails; `is_available=false` is set manually by an Operator if quality degradation is reported.

## Error code

`MODEL_NOT_APPROVED` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Operator re-downloads/re-verifies the checkpoint from a trusted source before re-registering.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
