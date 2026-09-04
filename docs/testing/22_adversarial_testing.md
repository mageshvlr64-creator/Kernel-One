# Adversarial Testing

> Deliberately hostile inputs beyond the specific `SEC-TEST-*` cases — fuzzing and red-team-
> style probing intended to find gaps the named threat model didn't anticipate.

## Method

1. Fuzz every API endpoint's request body against its schema (malformed JSON, wrong types,
   boundary values) — beyond `04_contract_testing.md`'s happy/sad-path pair, this generates a
   wide range of malformed inputs automatically.
2. Prompt-injection variants beyond `SEC-TEST-004`'s single example — a small corpus of known
   injection patterns tested against document ingestion and chat input.
3. Periodic manual red-team review of the full `security/02_threat_model.md` table, looking
   specifically for threats not yet in `reference/13_test_matrix.md`.

## Rule

Any adversarial test that finds a real gap produces: a new named `SEC-TEST-###` case added to
`testing/21_security_testing.md`, a new row in `security/02_threat_model.md` if it's a
genuinely new threat category, and a fix — in that order, not a silent patch without updating
the threat model.
