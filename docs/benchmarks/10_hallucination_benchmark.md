# Hallucination Benchmark

> Measures the rate of unsupported/fabricated claims — the failure mode
> `09_citation_benchmark.md` and REQ-FUNC-005 are both designed to catch, measured here as an
> aggregate rate across a test set for model-selection purposes.

## Method

A test set specifically designed to tempt fabrication (questions with no answer in the
provided source, ambiguous questions, questions about details not present in the document);
scored on: does the model correctly decline/hedge rather than confabulating an answer.

## Why this is a separate benchmark from citation accuracy

`09_citation_benchmark.md` measures citation quality *given that the model answered*; this
benchmark specifically measures whether the model recognizes when it should not answer at all
— a model could theoretically cite well when it does answer but still fail this benchmark by
answering confidently in cases it should have declined.
