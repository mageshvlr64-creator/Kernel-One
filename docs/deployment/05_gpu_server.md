# GPU Server Deployment

> Deployment notes specific to hosts with a dedicated GPU (PROFILE-B/C/D), as opposed to
> `06_cpu_only_demo.md`'s fallback path.

## GPU passthrough

The Inference Gateway's vLLM provider container requires GPU passthrough
(`--gpus all` in Docker, or the NVIDIA Container Toolkit equivalent) — this container is the
**only** one granted this elevated device access; every other service, especially the Code
Execution sandbox, has no GPU access at all (least privilege, `security/21_container_security.md`).

## VRAM allocation

If running both a text-capable and vision-capable model concurrently on a single GPU
(PROFILE-B, 12–16GB VRAM), the Model Router's resource-fit check
(`features/02_model_router/05_resource_fit.md`) must account for both models' combined
footprint, or the deployment must configure model-swapping (load/unload on demand,
`features/01_model_management/06_model_loading.md`/`07_model_unloading.md`) rather than
assuming both fit simultaneously — this is a deployment-time configuration decision, not
automatically resolved by the router.
