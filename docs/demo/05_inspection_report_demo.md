# Inspection Report Demo (Detailed Script)

> The scripted, line-by-line version of `01_demo_overview.md`'s primary scenario steps 1-11,
> for the presenter to follow verbatim during rehearsal and the live demo.

## Script

1. **(Say)** "I'm going to upload a real inspection report — this never leaves this machine."
   **(Do)** Upload `03_demo_data.md`'s primary document, tag `INTERNAL`.
2. **(Say)** "Watch the network panel — nothing changes while this processes." **(Do)** Wait
   for state progression to `READY`, pointing at the Network Sovereignty Panel remaining green.
3. **(Say)** "Now I'll ask it a real question." **(Do)** Type: "What findings indicate
   equipment below specification, and on what page?"
4. **(Say)** "Every claim it makes should be clickable." **(Do)** Click a citation, show the
   source page highlight.
5. **(Do)** Generate the DOCX findings summary artifact; open it to show it's a real,
   well-formed file.
6. **(Do)** Open the audit viewer, scroll through the event chain for this exact task.
7. **(Say)** "Now let's see what happens if someone without permission tries this." **(Do)**
   Switch to `RestrictedUser`, attempt the same artifact export, show the `POLICY_DENIED`
   message.

## Timing checkpoints

Steps 1-2 should complete within 90s (document processing); steps 3-4 within 60s (retrieval +
generation); total under 5 minutes per `REQ-PERF-001`.
