# Feature 01 — Model Router

## Purpose
Never hardcode "which model answers this." The router inspects a task, classifies it, and picks the smallest model capable of handling it — this is what keeps you inside the 8 GB demo budget and is a judge-visible differentiator ("AI automatically chooses the appropriate local model", not a model dropdown).

## How to build

1. **Model Registry** — a YAML/JSON file (or SQLite table) listing every available model with fields: `name, type, capabilities[], context_len, vision(bool), reasoning_tier, coding(bool), ram_mb, quantization, security_class`. Populate it with the 4 models from `02_STACK.md`.
2. **Classifier step** — before calling any LLM, run the incoming request through the smallest model (Qwen2.5-0.5B) or simple keyword/regex heuristics to tag it: `general | coding | document_qa | heavy_reasoning`. For a 14-day build, a heuristic classifier (keywords + presence of an uploaded file + presence of code fences) is acceptable and faster to get right than a learned classifier — don't over-engineer this.
3. **Routing table** — a plain mapping from tag → model name, read from the registry, e.g. `coding → qwen2.5-coder-1.5b`, `document_qa → qwen2.5-1.5b` (paired with RAG context), `heavy_reasoning → qwen2.5-3b`.
4. **Load/unload discipline** — wrap the inference call so only one "large" model (>1.5 GB) is resident at a time on the demo profile. If Ollama is your runtime, this is mostly free (Ollama unloads idle models); if using llama-cpp-python directly, explicitly release the model object between switches.
5. **Log the decision** — every routing decision (which model, why) becomes a step in the Agent Kernel's execution graph (see Feature 02) and a row in the audit log (Feature 10). This is what makes "AI automatically chooses" a provable claim in the demo, not a slide.

## Data/API contract

```json
// Router input
{"task_text": "...", "has_attachment": true, "attachment_type": "pdf"}
// Router output
{"selected_model": "qwen2.5-1.5b-instruct-q4", "tag": "document_qa", "reason": "attachment present, no code fence detected"}
```

## Failure conditions

| Failure | Cause | Mitigation |
|---|---|---|
| Wrong model picked for a coding request | Classifier heuristic too narrow (misses code without fences) | Add fallback: if response quality/format looks wrong, let the user manually override the tag once — log the override for later heuristic tuning |
| Demo machine runs out of memory mid-swap | Two models briefly resident during a switch | Explicitly unload/await confirmation the old model is released before loading the new one; never "preload" the next likely model speculatively on the 8 GB box |
| First response after a model switch is very slow | Cold-start load time (reading GGUF from disk) | Warm up all models once at server startup in low-priority background order OR accept and narrate a short "loading model" spinner in UI rather than hiding it |
| Router silently falls back to a model not in the registry | Hardcoded default string left in code from early dev | Registry lookup must raise/log an explicit error if a tag has no mapped model — never silently default |
| Routing decision not visible to judges | Decision made but not surfaced in UI/audit | Router must emit its decision as a first-class execution-graph step (see Feature 02), not just an internal log line |

## Definition of Done
A request tagged `coding` visibly routes to the coder model and a request tagged `document_qa` visibly routes to the general model, both shown in the live execution graph, both logged, and switching between them on the 8 GB profile doesn't exceed the memory ceiling in `03_HARDWARE_CONSTRAINTS.md`.
