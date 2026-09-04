# Multimodal Image/Drawing Analysis

> End-to-end workflow specification. References the specific features involved rather than
> restating their internal behavior.

## Requirements implemented

features/12_multimodal

## Steps

1. User uploads an equipment photograph or engineering drawing
2. Model Router selects a vision-capable model (schemas/06_model_schema.md capability='vision')
3. Agent analyzes the image, stating explicit confidence and limitations (features/12_multimodal/06_photo_analysis.md) — never claiming precision the model can't support
4. Result attached to the task as a Message with model_id populated

## Notes

See demo/07_multimodal_demo.md.
