# Failure Demo (Live Recovery Script)

> What to do if something goes wrong during the actual live demo — prepared in advance per
> `demo/01_demo_overview.md`'s closing note, not improvised on the day.

## Pre-planned fallbacks

| If this fails live... | Do this |
|---|---|
| Document processing takes too long / hangs | Switch to a pre-processed document already at `READY` state from an earlier rehearsal, narrate "let me use one I prepared earlier to keep us on time" |
| A model gives a poor/wrong answer | Have a second, verified-good question ready as a backup, move to it directly |
| Network/hardware issue on the primary machine | Switch to the backup environment (`02_demo_environment.md`) — this is why it exists pre-configured, not spun up live |
| Code execution demo's replanning doesn't trigger as expected | Have a pre-recorded screen capture of a successful run from rehearsal as a fallback to narrate over |

## Rule

Never attempt to debug a live failure in front of the audience — switch to the prepared
fallback immediately and keep the presentation moving; explain briefly and move on, don't
apologize extensively.
