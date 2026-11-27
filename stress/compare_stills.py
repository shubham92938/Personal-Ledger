"""Build V3/V4/V5/V6 comparison sheets and still metrics. No GL required."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

TIMES = [5, 20, 45, 180, 380, 630, 900, 1080]


def metrics(path):
    im = Image.open(path).convert("RGB")
    arr = np.asarray(im, dtype=np.float32) / 255.0
    lum = arr[:, :, 0] * .2126 + arr[:, :, 1] * .7152 + arr[:, :, 2] * .0722
    return {
        "file": path.name, "width": im.width, "height": im.height,
        "mean_luma": round(float(lum.mean()), 4),
        "shadow_fraction_below_0_02": round(float((lum < .02).mean()), 4),
        "highlight_fraction_above_0_98": round(float((lum > .98).mean()), 4),
        "edge_energy_proxy": round(float(np.abs(np.diff(lum, axis=0)).mean()
                                         + np.abs(np.diff(lum, axis=1)).mean()), 5),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stills", type=Path, required=True,
                   help="dir containing vN/vN-frame-XXXXX.png subdirs")
    p.add_argument("--out", type=Path, default=Path("out/compare"))
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    versions = ["v3", "v4", "v5", "v6"]
    font = ImageFont.load_default()
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except Exception:
        pass

    all_metrics = {}
    for ver in versions:
        d = a.stills / ver
        rows = []
        for t in TIMES:
            f = round(t * 24)
            pf = d / f"{ver}-frame-{f:05d}.png"
            if pf.exists():
                rows.append(metrics(pf))
        all_metrics[ver] = rows
    (a.out / "still-metrics.json").write_text(json.dumps(all_metrics, indent=2))

    # One grid sheet per timestamp: v3 | v4 | v5 | v6 side by side.
    for t in TIMES:
        f = round(t * 24)
        tiles = []
        for ver in versions:
            pf = a.stills / ver / f"{ver}-frame-{f:05d}.png"
            if not pf.exists():
                continue
            im = Image.open(pf).convert("RGB")
            tiles.append((ver, im.resize((620, 349), Image.Resampling.LANCZOS)))
        if not tiles:
            continue
        sheet = Image.new("RGB", (620 * len(tiles), 349 + 30), "#101214")
        d = ImageDraw.Draw(sheet)
        for i, (ver, im) in enumerate(tiles):
            sheet.paste(im, (i * 620, 0))
            d.text((i * 620 + 10, 350 + 6), f"{ver.upper()}  t={t}s  f={f}",
                   font=font, fill="#f0e6d2")
        sheet.save(a.out / f"version-compare-t{t:05d}.jpg", quality=92)
        print("SHEET", a.out / f"version-compare-t{t:05d}.jpg", flush=True)
    print("COMPARE_DONE", flush=True)


if __name__ == "__main__":
    main()
