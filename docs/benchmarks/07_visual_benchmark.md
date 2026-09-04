# Visual Benchmark

> Evaluates vision-language description accuracy for the `vision` capability slot, and is the
> prerequisite evaluation gate mentioned throughout `industrial/08..09` and `later/02, 04`
> before any structured (non-description) visual capability is promoted out of `later/`.

## Method

Fixed labeled images (equipment photos, drawings) with known-correct descriptions; scored on:
description accuracy, appropriate expression of uncertainty (does the model hedge on details
it can't confidently determine, per `industrial/09_drawing_understanding.md`'s required
caveat pattern), and absence of fabricated detail.

## Expansion path

`later/02_pid_analysis.md` and `04_drawing_intelligence.md` both name this file's expanded,
symbol/dimension-specific successor as their explicit prerequisite before those V2
capabilities can be built responsibly.
