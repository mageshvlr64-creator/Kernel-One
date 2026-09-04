# Reasoning Benchmark

> Evaluates general instruction-following and multi-step reasoning quality for the
> `general-reasoning` capability slot.

## Method

A fixed set of prompts requiring multi-step reasoning (not solvable by pattern-matching alone),
scored manually (V1) or via an automated rubric (V2, `later/11_advanced_model_benchmarking.md`)
on: correctness, instruction-adherence, and refusal-when-appropriate (e.g. does the model
correctly decline to answer when it lacks the information, consistent with REQ-FUNC-005's
spirit extended to general reasoning).

## V1 status

Informal, manual scoring against candidate models during DEC-013's evaluation — not yet an
automated, repeatable score.
