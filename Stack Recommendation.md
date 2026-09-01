# Stack Recommendation (locked for 8 GB / no-GPU demo, 16 GB / no-GPU dev)

Your source doc defaults to Python/FastAPI + vLLM/Ollama and assumes GPU access "eventually." You have none. vLLM is effectively CPU-hostile for this timeline — drop it. Everything below runs CPU-only on both your machines.

## Backend

- **Language/framework:** Python 3.11 + FastAPI (keep this — matches your source doc, huge ecosystem for docx/xlsx/OCR/RAG, and you don't need Rust's speed for a CPU-bound LLM demo where the model itself is the bottleneck, not your glue code).
- **Inference runtime:** **llama.cpp** (via `llama-cpp-python`) or **Ollama** running GGUF models, Q4_K_M quantization. Ollama is easier to demo (one command, model swapping, OpenAI-compatible API); llama-cpp-python gives you more control over context/threads if Ollama's overhead is too much for 8 GB. Pick Ollama first — switch only if the demo machine chokes.
- **Task queue / async:** plain `asyncio` + FastAPI background tasks. Don't add Celery/Redis — one demo machine, one process, unnecessary infra risk.
- **DB:** SQLite (via SQLModel or plain `sqlite3`) for audit log, RBAC, task state, approvals. Zero setup, file-based, survives the "no internet in the demo room" requirement trivially.
- **Vector store:** **ChromaDB** (embedded/local mode, SQLite-backed) or **FAISS** if Chroma's memory footprint is too heavy on 8 GB. Start with Chroma; it's less code.
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` (~90 MB, CPU-fast, good enough for a hackathon corpus).
- **OCR:** **Tesseract** (`pytesseract`) — CPU-only, no GPU needed, "good enough" for typed/scanned reports. Do NOT attempt a VLM (vision-language model) for document understanding on 8 GB CPU — see `03_HARDWARE_CONSTRAINTS.md`.
- **Sandboxed execution:** Python `subprocess` with `resource` limits (RAM/CPU/time caps) + a restricted builtins namespace, OR `firejail` if available on the demo machine. Do NOT reach for Docker-in-Docker on the demo laptop — assume you can't guarantee Docker is installed/allowed in the venue.
- **Artifact generation:** `python-docx`, `openpyxl`, `reportlab` (or `fpdf2`) for PDF.

## Models (all CPU, all quantized GGUF, all swappable via the router — never hardcode)

| Role | Model | Approx RAM (Q4_K_M) |
|---|---|---|
| General reasoning / chat | Qwen2.5-1.5B-Instruct | ~1.2 GB |
| Heavier reasoning (only when needed) | Qwen2.5-3B-Instruct | ~2.2 GB |
| Coding | Qwen2.5-Coder-1.5B-Instruct | ~1.2 GB |
| Classification/routing (tiny, fast) | Qwen2.5-0.5B-Instruct | ~0.5 GB |
| Embeddings | all-MiniLM-L6-v2 | ~0.2 GB |

Nothing here exceeds ~2.5 GB resident, leaving headroom on the 8 GB demo box for the OS, FastAPI, and Chroma. **Never load two of the larger models simultaneously on the demo machine** — the router must unload/swap, not stack.

## Frontend

- Plain **React (Vite)** or even server-rendered HTML + HTMX if you want to cut build complexity — you don't need a fancy SPA framework to render a chat pane + a live execution-graph checklist + a file-download button. Pick React only if you're already fluent in it; otherwise HTMX saves you a day.
- WebSocket for live execution-graph updates (native `WebSocket` API, no library needed).

## What to explicitly NOT use (from your original doc, given your hardware)

- vLLM (built for GPU-batched serving; wrong tool for single-CPU-box demo)
- Any VLM/multimodal image model (needs GPU memory bandwidth you don't have; Tesseract OCR covers the "read a document" demo need)
- Docker-based sandbox (venue/setup risk on a laptop you don't fully control)
- NVIDIA NIM (explicitly GPU-only, your source doc already says skip it)
- Kimi K2 / any >7B model (your source doc already flags this — don't chase it)
