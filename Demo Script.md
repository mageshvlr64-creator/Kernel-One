# Demo Script — What Judges See

Your source doc's real insight (Section 31): don't say "we use open-source LLMs / we have RAG / we have agents / we're local" — everyone building on Open WebUI-adjacent stacks can claim that. Say and SHOW: **"a sovereign execution environment for AI agents"** — meaning every step is visible, permissioned, and audited.

## The single demo flow (5-7 minutes)

1. **Upload a scanned "confidential" inspection report (image/PDF).**
   Narrate: "This never leaves this laptop. No internet call happens during this entire demo — watch the sovereignty monitor."
2. **Ask: "Summarize the findings and draft an approval note."**
   The UI shows the live execution graph appearing step by step:
   `✓ Document loaded → ✓ OCR completed → ✓ N findings extracted → ✓ Router selected qwen2.5-1.5b → ✓ Findings cross-checked against retrieved context → ⚠ Human approval required`
3. **Click "Approve."** Graph continues: `✓ DOCX generated`. Download the real .docx.
4. **Open the Audit tab.** Show the immutable log of every step just performed, timestamped.
5. **Second mini-demo (coding agent):** "Fix this Python script" → sandbox runs it, shows the tool call in the graph, shows RBAC blocking the same action for a "restricted" demo user.
6. **Close on the sovereignty monitor panel:** zero outbound requests logged for the whole session.

## Why this ordering

- Leads with the visual (execution graph) that no generic chatbot UI has — this is what makes judges lean forward.
- Uses your actual hardware honestly (small local model, CPU) rather than promising something you can't run live — a judge asking "what GPU is this on" and hearing "none, it's fully CPU, that's the point" is a strength, not a weakness, given the "sovereign/air-gapped" pitch.
- Ends on audit + sovereignty because that's the differentiator claim — prove it, don't just say it.

## Have ready as backup

- The screen recording from `03_HARDWARE_CONSTRAINTS.md`'s fallback plan.
- A pre-uploaded document so you're not waiting on a live upload+OCR pass if time is short.
