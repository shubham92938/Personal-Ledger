"""Stills only: render film times with the v4 stage. No video is produced."""
import sys, argparse
from pathlib import Path
ROOT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / 'engine')]
from PIL import Image

p = argparse.ArgumentParser()
p.add_argument('--times', required=True)
p.add_argument('--width', type=int, default=960)
p.add_argument('--outdir', type=Path, required=True)
p.add_argument('--stage', default='v4', choices=['v3', 'v4'])
a = p.parse_args()
a.outdir.mkdir(parents=True, exist_ok=True)

import build_film_v3 as film
if a.stage == 'v4':
    from stage_cine_v4 import Stage
else:
    from stage_cine_v3 import Stage
w = a.width; h = w * 9 // 16
stage = Stage({'wide': (w, h)})
for t in [float(x) for x in a.times.split(',')]:
    f = round(t * 24)
    if f > 0:  # warm up the previous frame for camera motion blur history
        prev = film.scene((f - 1) / 24); stage.shadow(prev, f - 1); stage.frame(prev, 'wide')
    cur = film.scene(f / 24); stage.shadow(cur, f)
    raw = stage.frame(cur, 'wide')
    img = Image.frombytes('RGBA', (w, h), raw).transpose(Image.Transpose.FLIP_TOP_BOTTOM).convert('RGB')
    path = a.outdir / f'frame-{f:05d}.png'
    img.save(path)
    print('STILL', path, cur.name, flush=True)
