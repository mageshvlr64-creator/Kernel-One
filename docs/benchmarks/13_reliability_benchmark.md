# Reliability Benchmark

> Measures crash/failure rate under sustained use — feeds `failures/11_model_corruption.md`'s
> "quality degradation" detection and general model-selection confidence.

## Method

Run the candidate model against a sustained stream of realistic requests (mirroring
`testing/25_load_testing.md`'s load pattern) over an extended period; track: crash rate,
malformed-response rate (triggering `failures/07_model_failures.md`), and any observed
degradation over time (e.g. memory leak in the runtime, not the model itself, though this
benchmark would surface either).
