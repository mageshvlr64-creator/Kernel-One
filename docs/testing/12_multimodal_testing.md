# Multimodal Testing

> Covers `features/12_multimodal/` — vision-capable model integration and the required
> caveat pattern (`industrial/09_drawing_understanding.md`).

## Required tests

- A vision-capable model correctly receives an image + text prompt and returns a response
  (mocked at the model layer for determinism, per `07_agent_testing.md`'s approach).
- Responses for dimension/quantitative claims include the required "unverified, confirm
  against source" caveat (`industrial/09_drawing_understanding.md`) — checked as a
  response-content assertion, not just an infrastructure test.
