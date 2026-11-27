# Cinematic 3D upgrade package: V5

This archive keeps the original V3/V4 project and adds a small V5 shader
stability pass. Start with `V5-CHANGES.md`, then `V5-REVIEW-CHECKLIST.md`.

## Validate source

```bash
python validate_v5.py
```

This performs Python syntax and exact patch-target checks. It does not need an
OpenGL context and does not render images.

## Render comparison stills

Install the runtime packages in `requirements-v5.txt` and ensure a working
ModernGL/EGL or supported OpenGL environment is available. Then run the three
A/B commands in `V5-CHANGES.md`.

The current editing environment did not have `moderngl`, so V5 shader
compilation and image output were not verified here. Do not treat source
validation as a visual approval. Use the review checklist and inspect actual
moving footage before a full-length render.
