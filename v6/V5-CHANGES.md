# V5 cinematic stability pass

V5 is a conservative follow-up to V4. It does not replace V3/V4, alter scene
geometry, change the narration, retime any mechanism, or claim to be a final
master.

## Changes

1. **World-anchored shadow rotation.** V4 rotated its 12 shadow taps using
   `gl_FragCoord`, so the sampling pattern was screen-space and could crawl
   across surfaces during a camera move. V5 derives the rotation from the
   receiver's world position. The pattern should remain attached to the
   scene rather than the display.
2. **Stable fine grain.** V4 changed its grain pattern every frame. V5 keeps
   the subtle grain spatially stable to avoid adding unnecessary flicker to
   gradients and dark areas.

## What V5 deliberately does not claim

- It does not add geometry, physically based refraction, volumetric water,
  glass thickness, or new material maps.
- It does not change the camera path, animation, scene composition, or
  historical interpretation.
- Shader stability is not proof of visual quality. World-space sampling can
  reveal spatial patterns on large surfaces; inspect moving shots for this.
- The package still requires real-time playback review for shadow crawling,
  aliasing, motion blur, focus, exposure, color, captions, sound, and continuity.

## A/B still comparison

From this folder:

```bash
python render_v5_stills.py --stage v3 --times 5,20,45,180,380,630,900,1080 --outdir review/v3
python render_v5_stills.py --stage v4 --times 5,20,45,180,380,630,900,1080 --outdir review/v4
python render_v5_stills.py --stage v5 --times 5,20,45,180,380,630,900,1080 --outdir review/v5
```

Use identical times and width for all three passes. Compare at 100% and at
normal playback size. Stills cannot validate temporal stability; render short
moving clips around the fastest camera arcs before committing to a full render.

## Safety and provenance

V5 is additive. The existing V3/V4 files and source assets are retained.
No full video render, audio replacement, upload, or publication is performed
by these scripts.
