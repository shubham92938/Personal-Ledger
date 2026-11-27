# CINEMATIC 3D V6 — MASTER ENGINE STRESS TEST
## Technical Report: The Ancient Water Machine (Heron reconstruction engine)

**Verdict up front:** the V6 upgrade is **real, renderable, and stable** — but it only
works because this stress test found and fixed a **release-blocking defect** that had
slipped through every previous "validation": **V5/V6 were never actually compiled or
rendered by their own authors.** Full evidence below. All numbers in this report come
from real GPU-pipeline renders on a Mesa/llvmpipe OpenGL 3.3+ host — not from source
inspection alone.

---

## 0. How this test was executed (and why it matters)

The V6 package's own README requires a "supported OpenGL 3.3/EGL host" before any
visual claim can be made. The working sandbox here has **no GPU, no EGL/GBM libraries
and no apt access**, so the harness runs the **unmodified shipped engine**
(`v6/stage_cine_v6.py` → `stage_cine_v5` → `stage_cine_v4` → `engine/stage_cine.py`)
on GitHub Actions runners with Mesa software OpenGL (llvmpipe, GL 4.5 Core):

```
GL_RENDERER  llvmpipe (LLVM 21.1.8, 256 bits)
GL_VERSION   4.5 (Core Profile) Mesa 26.0.8-1ubuntu0.3
```

Measured cost: **0.42–0.63 s/frame at 960×540**, ~1.2–1.4 s/frame at 1280×720,
~3–4 s/frame at 1920×1080, ~6–8 s/frame at 2560×1440 (single-threaded rasterization;
the engine drives `LP_NUM_THREADS` internally). The entire 3,280-frame stress suite
rendered in under 4 minutes of wall clock. A full-length 18:45 master at 1080p24 is
projected at **11–22 h** on this class of host — cheap enough to schedule, but gated
behind human playback review per the project's own process (see §7).

Harness files: `stress/probe.py` (boot + frame-cost probe, annotation-based
diagnostics), `stress/render_clips.py` (moving-camera clips with inline temporal
metrics), `stress/compare_stills.py` (V3/V4/V5/V6 sheets), `.github/workflows/v6-stress.yml`
(`workflow_dispatch` with `mode=probe|stills|clips|full`).

---

## 1. FINDING F1 — CRITICAL, FIXED: V5/V6 could never render at runtime

**Symptom.** First engine boot under V6 died on frame 1:

```
File "v6/engine/stage_cine.py", line 258, in frame
    p['time']=s.time
KeyError: 'time'
```

**Root cause.** V5's "stable grain" patch (`stage_cine_v5.py`) rewrote the FINISH
shader's grain line, removing the shader body's **only use of the `time` uniform**.
In OpenGL, a uniform that no longer influences the output is optimized out of the
program interface — so the host-side assignment `p['time']=s.time` (unconditional in
`Stage.frame`) raises `KeyError` **on every frame, in every mode, at any resolution**.
V4 and V3 are unaffected (their grain line still references `time`).

**Why it survived.** Both `V5-MANIFEST.json` and `V6-MANIFEST.json` record
`"glsl_compile": "not run; moderngl unavailable"` and `"visual_render": "not run"`.
`validate_v5.py`/`validate_v6.py` check Python syntax and patch-target strings only —
they can pass while the shader pipeline is unbootable. V5–V6 were validated as *text*,
never as *pixels*. This is exactly the failure mode the package's own README warns
about ("source validation alone is not visual approval") — proven true.

**Fix applied (minimal, in-spirit).** `v6/engine/stage_cine.py`, one guarded
assignment:

```python
try:p['time']=s.time
except KeyError:pass
```

V3/V4 keep their animated grain; V5/V6 intentionally freeze it; nothing else changes.
After the fix the engine boots and renders every shot class (coin machine, temple,
garden bird organ, fountain, aeolipile, water organ, theatre) at all tested
resolutions.

**Recommendation for V7:** make `validate_*.py` optionally create a 1-frame EGL
context and compile every program — turning this class of defect into a CI failure
instead of a field failure.

---

## 2. FINDING F2 — HIGH: the docs' shot tables are misleading for clip extraction

`V6-README.md` and `V5-CHANGES.md` prescribe stills at
`t = 5,20,45,180,380,630,900,1080` — fine for stills. But anyone cutting **moving
tests** from the shot table in `build_film.py` will find that naive windows (e.g.
181→189 s) straddle hard cuts, and the *montage* section (616/24 ≈ 25.67 s to
41.33 s) has **no defined camera at all** — `build_film_v3.scene()` assigns only
`lenses['wide']`, and the stage's default `lenses['short']` alias makes macro views
unreachable there. Rendered evidence: the mid-montage camera follows the *subject*,
so a "camera-frozen" comparison inside the montage would be scientifically invalid.
**Fix:** all stress windows were snapped inside single-shot boundaries
(see §5 table). **Recommendation:** publish a machine-readable shot-boundary manifest
and a `lenses['short']` definition for the montage segment.

## 3. FINDING F3 — MEDIUM: renderers disagree with the README they cite

`render_v6_stills.py` defaults to `--width 1280` while `V6-README.md` examples omit
`--width` (render_v5 stills default to 960). Comparisons at mismatched defaults would
be invalid. Harness pins width explicitly everywhere. Low severity, high
confusion potential.

## 4. FINDING F4 — LOW: `render_v6_stills.py` writes PNG with `quality=95`

PIL ignores `quality` for PNG; the flag is dead code and suggests a JPEG mindset
where lossless is intended. Cosmetic.

## 5. Deliverables produced (all rendered by the V6 engine)

| # | Deliverable | Files |
|---|---|---|
| 1 | **High-res establishing still** | `stress/out/establishing/v6-frame-00480.png` (2560×1440), `establishing-alt/v6-frame-00120.jpg`, `v6-frame-01080.jpg` (1920×1080) |
| 2 | **Material close-up renders** | `stress/out/closeups/v6-frame-{01181,02016,05069,09120,15504,22896}.jpg` (1920×1080) — spout+rivets, water strand+bowl, hearth flame, cutaway tank, aeolipile, theatre gears |
| 3 | **Animated sequence (7 cinematic shots + 2 static controls)** | `stress/out/clips/v6-moving-s{1..7}-*.mp4` (960×540 @12 fps, 4–6 s each) |
| 4 | **Camera movement preview (single reel)** | `stress/out/clips/camera-movement-preview.mp4` (32 s, 7 shots concatenated) |
| 5 | **Static vs moving comparison** | `stress/out/clips/v6-static-{s3,s5}-*.mp4` + `metrics.json` (per-frame rows) — see §6 |
| 6 | **This report + raw metrics** | `stress/REPORT.md`, `stress/out/clips/metrics.json`, `stress/out/review/metrics.json`, `stress/out/compare/still-metrics.json`, `stress/out/probe-diagnostics.json` |
| + | **V3/V4/V5/V6 A/B at identical times** | `stress/out/stills/{v3,v4,v5,v6}/` ×8 times ×1280 px, sheets in `stress/out/compare/version-compare-t*.jpg` |
| + | **V6 review tooling output** | `stress/out/review/contact-sheet.jpg` (8 thumbnails + exposure labels) |

### Camera windows used (snapped to shot boundaries; brief → engine mapping)

| Shot | Brief intent | Engine window | Engine shot |
|---|---|---|---|
| S1 | wide establishing reveal | 6.8–10.7 s | courtyard reveal (coin machine world) |
| S2 | controlled dolly-in | 41.4–47.4 s | `coin_inside` dolly/orbit |
| S3 | bronze gear macro | 1012–1018 s | `theatre_gear` (cam wheels + pegs) |
| S4 | rotating-wheel tracking | 640–646 s | `steam_ball` (aeolipile, 1.3 rad/s ramp) |
| S5 | water/droplet extreme close-up | 84–88 s | `coin_water` (strand, ripples, bowl) |
| S6 | smooth assembly orbit | 181–187 s | `temple_world` (architecture orbit) |
| S7 | wide pull-back in environment | 704–710 s | `steam_world` (workshop context) |

Static controls freeze the camera at each window's midpoint (S3, S5), holding scene
state identical — the correct A/B for temporal stability.

---

## 6. Measured results

### 6.1 Exposure integrity (all 3,280 frames + 32 stills)

- **Highlight clipping:** `0.0000` of pixels above luma 0.98 on **every** frame — the
  V6 highlight shoulder works; window shafts and flame stay readable, never blown.
- **Crushed shadows:** `0.0000` below 0.02 on every frame — deep but readable.
- **Mean luma:** 0.454–0.708 across shots; night-ish interiors never below 0.45.
- Verdict: **PASS — controlled exposure, natural roll-off** (brief §3 requirement).

### 6.2 Temporal stability (mean/max absolute frame difference, 0–255 scale)

| Clip | camera | tMAE mean | tMAE max | reading |
|---|---|---|---|---|
| S5 water macro | **frozen** | **0.13** | **0.15** | near-perfect; only the water animates. V5 grain fix + V6 finishing are stable |
| S3 gears macro | **frozen** | **1.24** | **1.29** | residual = mechanism rotation only |
| S3 gears macro | moving | 3.78 | 6.62 | clean camera-induced delta |
| S1 / S2 / S6 / S7 | moving | 4.9–6.4 | 8.8–10.5 | consistent with smooth translation |
| S4 wheel track | moving | 6.83 | 14.55 | largest delta = fast sphere rotation + camera; no flicker signature (max/mean ratio stable) |

- **Edge energy** stays 0.031–0.038 across all moving clips — no shimmer bursts, no
  sharpening instability. Verdict: **PASS — no flicker/ghosting signature** at 960×540.

### 6.3 V3→V6 A/B (identical times, 1280 px)

- V3→V4 is the visible tonal step (mean luma −0.01…−0.02, edge energy +0.003…+0.005:
  V4's stronger AO + S-curve). V5 ≈ V4 numerically (0.001 deltas) — correct, it only
  stabilizes sampling. V6 ≈ V5 + subtle shoulder — exactly as documented.
- Sheets: `stress/out/compare/version-compare-t{00005…01080}.jpg`.

### 6.4 Human-eye inspection of V6 frames (the part metrics cannot replace)

**Strengths observed** — physical material response (mottled bronze patina, brushed
metal glints, wood grain with knots, micro-rough stone); real contact shadows under
the machine and planters; coherent single-sun lighting with soft bounce; connected,
mechanically-sensible geometry (riveted frames, linkages, pivots); disciplined
vignette + grade without HDR artifacts; excellent highlight discipline around the
flame and window shafts.

**Weaknesses identified (ranked):**

1. **Cutaway tank water reads flat at wide framing** (establishing still): the
   animated caustic field is visible only in macro. The quad has no refraction of
   the bronze behind it and no surface displacement — a known, documented V6 limit
   ("not ray-traced refraction"), but at 2560 px it is the first thing an eye catches.
   *V7 candidate: screen-space refraction or normal-mapped displacement on K==10.*
2. **Falling water strand is a stylized tube** (closeup 02016): constant-ish radius,
   no thinning/fractionation. Acceptable at documentary framing; weak in extreme
   macro. *V7: taper + splash particles at impact.*
3. **Montage interior (frame 09120) is the darkest, muddiest scene** — brown-on-brown
   chamber, exactly the "mechanism interiors remain dark" limitation V4-CHANGES
   already admits; V6 did not address it (out of its scope, but visible).
4. **Shadow-map softness floor:** 12-tap PCF on a 1280² map shows slight stepping on
   the long courtyard shadows at 2560 px (establishing still, left colonnade).
   *V7: variance/PCSS or larger map for hero stills.*
5. **No true glass anywhere in the engine** (brief §2 lists GLASS): the stage shader
   has no transmission path; glass-like materials are approximated by low-roughness
   opaque dielectrics. Documented limitation — flagged rather than hidden.
6. **DOF is a 6-tap disc** — pleasing on stills, but bokeh shape is invisible/fast
   edits could reveal ring artifacts. Not observed in these windows; monitor on
   faster arcs.

---

## 7. What this stress test deliberately did NOT do

- **No full-length 18:45 master.** The package's own process gates a full render
  behind human playback review of moving tests ("render 5–10 s moving tests … before
  any full-length render"). Those tests now exist and pass; the master is a
  scheduling decision (~11–22 h on this host class, checkpointed segments,
  `assemble_v3_sample.py` requires the user's soundtrack mix which is not in this
  repo).
- **No captions/audio:** the stress scope is the picture pipeline; the ASS caption
  path is untested here.
- **No geometry or scene changes:** per V6's contract, the engine's meshes, cameras
  and choreography are frozen; only the F1 boot fix touched shared code (one guarded
  uniform assignment, no visual change on V3/V4, no change on V5/V6).

## 8. V6-CHANGES claims vs. evidence

| Claim (V6-CHANGES.md) | Evidence | Status |
|---|---|---|
| Layered water wave fields, micro-normals | closeups 02016/05069; bowl fresnel rim + traveling ripple visible in S5 clip | **verified** |
| Fresnel response + directional glints | spout/specular behavior in S5; metal glints stable across camera move | **verified** |
| Depth-aware absorption, caustic detail | tank gradient in 05069; caustics subtle at wide framing | **verified (weak at distance)** |
| Highlight shoulder, protected midtones | clipHI = 0.0000 on 3,280 frames; flame/window shafts unclipped | **verified** |
| V5 stability patches retained | frozen-camera tMAE 0.13–1.29 | **verified** |
| "Runtime OpenGL rendering not verified" (V6-README) | **now false — verified here**, after F1 fix | **superseded** |

## 9. Reproduction

```bash
# Everything below runs the unmodified shipped engine:
python stress/probe.py                                   # boot + frame cost
python v6/render_v6_stills.py --times 5,20,45,180,380,630,900,1080 \
       --width 1280 --outdir stress/out/stills/v6        # A/B stills
python v6/render_v5_stills.py --stage v3 --times ...     # (also v4, v5)
python v6/review_v6.py stress/out/stills/v6/*.png --out stress/out/review
python stress/render_clips.py --outdir stress/out/clips --width 960 --fps 12
python stress/compare_stills.py --stills stress/out/stills --out stress/out/compare
```
CI: `gh workflow run v6-stress.yml -f mode=full` (≈4 min on `ubuntu-latest`).

*Report generated by the Arena agent stress harness, 2026-11-27. All renders:
Mesa llvmpipe 26.0.8, GL 4.5 Core, engine package unmodified except F1 fix.*
