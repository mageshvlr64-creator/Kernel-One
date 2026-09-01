# Hardware Constraints — Read This Before Picking Any Model or Library

**Dev machine:** 16 GB RAM, no GPU.
**Demo machine:** 8 GB RAM, no GPU.
**Design rule: build and test against the 8 GB demo profile, not the 16 GB dev profile.** If it only runs on the dev box, it doesn't exist for judging day.

## Hard ceilings

- Total resident model memory on the demo machine should stay **under ~3 GB** at any single point in time, leaving room for the OS (~1-1.5 GB), Python/FastAPI/Chroma (~0.5-1 GB), and browser (~0.5-1 GB) on an 8 GB box. This is why the model table in `02_STACK.md` tops out around 2.2 GB per model and why the router must not run two large models concurrently.
- CPU-only inference means **latency, not throughput, is your enemy**. A 1.5B Q4 model on a modern CPU gives usable (a few seconds) responses for short generations. A 3B model is noticeably slower — reserve it for the one "heavy reasoning" demo moment, not every turn.
- No GPU means no VLM-based document/image understanding at usable speed. This is the single biggest scope cut from your original 4000-line doc: **use OCR (Tesseract) + text-based reasoning, not a vision model**, for the "understand this scanned report" feature.

## Specific things ruled OUT and why

| Ruled out | Why |
|---|---|
| gpt-oss-20B | Needs ~16 GB just for the model, leaving nothing for OS/app on either machine, let alone the 8 GB demo box |
| Any VLM (LLaVA, Qwen-VL, etc.) even "small" variants | Vision models are memory- and compute-heavy per token; CPU inference is too slow for a live demo |
| vLLM | Built around GPU batched KV-cache serving; adds complexity with zero benefit on CPU |
| Local ASR (Whisper large/medium) | Whisper-small/tiny is fine on CPU if you want speech input as a stretch goal; anything bigger will lag badly live |
| Docker-based sandbox | Extra install/permission dependency you can't guarantee at the venue; use process-level sandboxing instead |
| Running the vector DB and 2 LLMs loaded at once on demo box | Will swap/thrash on 8 GB; router must load-on-demand and unload after use |

## Testing discipline

- **Every feature you build must be smoke-tested on an 8 GB-equivalent budget**, not just on your 16 GB dev machine. If you don't have a second physical 8 GB box to test on until later, artificially cap memory during dev (e.g. run your process in a cgroup/container with a 8 GB limit, or close everything else and watch RAM in a task monitor while running the full pipeline end-to-end).
- Time-box every model call. If a response takes >15-20 seconds on the demo hardware, that's a live-demo failure risk — fall back to a smaller model for that role rather than hoping the judges are patient.

## The fallback plan if the demo machine turns out to be worse than expected

Keep a **pre-recorded terminal/screen capture of the full pipeline running successfully** as an insurance policy. This is standard hackathon practice, not cheating — you still demo live first, but you're not sunk by a flaky Wi-Fi/venue laptop.
