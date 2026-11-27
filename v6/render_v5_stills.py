"""Render V3, V4 or V5 comparison stills; this script never produces a video."""
import argparse
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / "engine")]

p = argparse.ArgumentParser()
p.add_argument("--times", required=True, help="Comma-separated film times in seconds")
p.add_argument("--width", type=int, default=960)
p.add_argument("--outdir", type=Path, required=True)
p.add_argument("--stage", default="v5", choices=["v3", "v4", "v5"])
a = p.parse_args()
if a.width < 320 or a.width > 3840:
    p.error("--width must be between 320 and 3840")
times = [float(x.strip()) for x in a.times.split(",") if x.strip()]
if not times or any(t < 0 for t in times):
    p.error("--times must contain one or more non-negative seconds values")
a.outdir.mkdir(parents=True, exist_ok=True)

import build_film_v3 as film
if a.stage == "v5":
    from stage_cine_v5 import Stage
elif a.stage == "v4":
    from stage_cine_v4 import Stage
else:
    from stage_cine_v3 import Stage

w = a.width
h = w * 9 // 16
stage = Stage({"wide": (w, h)})
for t in times:
    frame = round(t * 24)
    if frame > 0:
        prev = film.scene((frame - 1) / 24)
        stage.shadow(prev, frame - 1)
        stage.frame(prev, "wide")
    current = film.scene(frame / 24)
    stage.shadow(current, frame)
    raw = stage.frame(current, "wide")
    image = Image.frombytes("RGBA", (w, h), raw).transpose(
        Image.Transpose.FLIP_TOP_BOTTOM
    ).convert("RGB")
    path = a.outdir / f"{a.stage}-frame-{frame:05d}.png"
    image.save(path)
    print("STILL", path, current.name, flush=True)
