"""Render deterministic V6 review stills. Requires moderngl + EGL/OpenGL 3.3."""
import argparse
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / "engine")]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--times", required=True, help="Comma-separated film times in seconds")
p.add_argument("--width", type=int, default=1280)
p.add_argument("--outdir", type=Path, required=True)
a = p.parse_args()
if not 320 <= a.width <= 3840:
    p.error("--width must be between 320 and 3840")
try:
    times = [float(x.strip()) for x in a.times.split(",") if x.strip()]
except ValueError:
    p.error("--times must contain numeric seconds")
if not times or any(t < 0 for t in times):
    p.error("--times must contain one or more non-negative values")
a.outdir.mkdir(parents=True, exist_ok=True)

import build_film_v3 as film
from stage_cine_v6 import Stage

w, h = a.width, a.width * 9 // 16
stage = Stage({"wide": (w, h)})
for t in times:
    frame = round(t * 24)
    if frame > 0:
        previous = film.scene((frame - 1) / 24)
        stage.shadow(previous, frame - 1)
        stage.frame(previous, "wide")
    current = film.scene(frame / 24)
    stage.shadow(current, frame)
    raw = stage.frame(current, "wide")
    image = Image.frombytes("RGBA", (w, h), raw).transpose(Image.Transpose.FLIP_TOP_BOTTOM).convert("RGB")
    path = a.outdir / f"v6-frame-{frame:05d}.png"
    image.save(path, quality=95)
    print(f"STILL {path} | {current.name} | t={t:.3f}s", flush=True)
