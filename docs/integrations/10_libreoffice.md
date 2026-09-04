# LibreOffice Integration

> Used headlessly for DOCX/PPTX/XLSX-to-PDF conversion where needed
> (`features/15_artifact_engine/06_pdf_generation.md`) and as a validation step (opening a
> generated Office file to confirm it's well-formed, `runtime/_state_machines_canonical.md#artifact`
> VALIDATING state).

## Invocation

Headless conversion via `soffice --headless --convert-to pdf` (or the equivalent API binding),
run inside a resource-limited subprocess with its own timeout
(`artifact-generation` operation class, `runtime/11_retry_policy.md`) — a hung LibreOffice
process is killed at that timeout, not left running indefinitely.

## Failure modes

See `failures/33_pdf_generation_failures.md`.
