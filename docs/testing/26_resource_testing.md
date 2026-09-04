# Resource Testing

> Verifies `performance/03_memory_budgets.md`/`04_cpu_budgets.md`/`05_gpu_budgets.md` are
> accurate under real operation, and that resource limits (especially the Code Execution
> sandbox's hard limits) actually enforce at the stated values.

## Required tests

- Long-running soak test (hours, not seconds) confirming no memory leak in any long-lived
  service — a service's RSS should stabilize, not grow unboundedly.
- Sandbox resource limit verification: a container attempting to exceed its configured
  CPU/memory limit is actually killed at that limit, not at some looser effective limit due to
  a misconfiguration.
