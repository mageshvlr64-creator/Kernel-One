# Approval Demo

> A focused walkthrough of `ui/11_approval_ui.md`, usable standalone or as an extension of the
> primary scenario's approval step if it's triggered.

## Script

1. **(Say)** "High-risk actions don't just happen — a human has to say yes." **(Do)** Trigger
   an action requiring approval (e.g. exporting a CONFIDENTIAL-tagged artifact).
2. **(Do)** Switch to the Approval Panel, show the pending request with its full context.
3. **(Do)** Approve it, show the gated action then proceeding.
4. **(Optional)** Show a rejection instead, and the gated action failing cleanly with a clear
   reason.
