# Sandbox Testing

> Covers `features/09_code_execution/` isolation guarantees specifically — the highest-stakes
> test file in this directory given REQ-SEC-002.

## Required tests (`TEST-SANDBOX-001..004`)

1. Network isolation: `SEC-TEST-003` — generated code cannot reach any host.
2. Resource limits: code attempting to exceed CPU/memory/process-count limits is killed with
   `SANDBOX_LIMIT_EXCEEDED`, not allowed to degrade the host.
3. Filesystem isolation: code cannot read/write outside its task workspace mount.
4. Cleanup: container is fully removed after execution (`features/09_code_execution/11_container_cleanup.md`)
   — no orphaned containers accumulate across repeated test runs.
