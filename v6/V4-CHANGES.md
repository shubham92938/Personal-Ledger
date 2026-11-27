# v4 stage upgrade (stills-verified only)

Files: `stage_cine_v4.py` (exact-string shader patches over the frozen v3 engine),
`render_v4_stills.py` (stills only; `--stage v3` renders the original for A/B).
Original `original-film-source/` is untouched. No video was rendered (storyboard gate).

## Changes
1. Cutaway water: depth gradient + animated caustic shimmer + fresnel rim (was flat cyan).
2. Shadows: 5 fixed taps -> 12 per-pixel rotated taps (softer, less banding).
3. Ambient: stronger sky-blue top light, warm ground bounce.
4. Ambient occlusion: wider second ring, sampled as opposite pairs (min of both sides)
   so grazing floors are not falsely darkened. First attempt used single samples and
   produced a visible pale disc on the floor; bisected (V4_SKIP=ao) and fixed.
5. Bloom: two extra wide rings, higher gain.
6. Grade: cool shadows / warm highlights, gentle S-curve, stronger vignette.

## Known limits (not fixed)
- Cutaway water is still a flat quad; real depth needs new geometry/refraction.
- Mechanism interiors remain dark and brown; they need authored fill lights/materials.
- Environments (walls, sky, props) are unchanged: no new geometry was added.
- Camera/animation timing is unchanged.
- Checked on 3 stills at 960px only. Motion, flicker of the per-pixel shadow
  rotation across frames, and 1080p behaviour are NOT verified.
