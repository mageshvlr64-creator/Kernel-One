# Report Generation

> End-to-end workflow specification. References the specific features involved rather than
> restating their internal behavior.

## Requirements implemented

features/15_artifact_engine

## Steps

1. Agent's findings/answers are compiled into a structured DOCX
2. Artifact classification computed as max(cited Evidence classifications) per REQ-DATA-001
3. If classification >= CONFIDENTIAL, export requires Approval (features/16_human_approval/)

## Notes

—
