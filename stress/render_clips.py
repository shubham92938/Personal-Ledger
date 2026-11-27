"""V6 moving-camera test clips with inline temporal metrics.

Renders the shipped V6 engine (stage_cine_v6 + build_film_v3 choreography) over
selected film windows. Windows are chosen to exercise the camera tests in the
master stress brief:

  s1  wide establishing reveal of the mechanical chamber
  s2  controlled dolly-in toward the machine
  s3  macro of bronze gears / cam mechanism engaging
  s4  tracking shot of the rotating wheel element (aeolipile sphere)
  s5  extreme close-up of flowing water and droplets
  s6  smooth orbit around the mechanical assembly
  s7  wide pull-back style shot of the machine in its environment

A subset is additionally rendered with the camera FROZEN at the window
midpoint, giving a static-vs-moving comparison at identical scene state.

Adaptive quality: if the measured frame cost projects past the wall-clock
budget, fps/window/width are stepped down and the decision is logged.

Per-frame metrics (exposure, clipping, edge energy, temporal MAE) are computed
inline and written to metrics.json — they are screening signals, not approvals.
"""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
V6 = HERE.parent / "v6"
sys.path[:0] = [str(V6), str(V6 / "engine")]

WINDOWS = [
    ("s1-establishing", 6.8, 10.7),
    ("s2-dolly-machine", 41.3, 47.3),
    ("s3-gears-macro", 1012.0, 1018.0),
    ("s4-wheel-track", 640.0, 646.0),
    ("s5-water-macro", 84.0, 88.0),
    ("s6-orbit", 181.0, 187.0),
    ("s7-pullback-wide", 704.0, 710.0),
]
STATIC = {"s3-gears-macro", "s5-water-macro"}


def encode(width, height, fps, path, ffmpeg):
    return subprocess.Popen(
        [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
         "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{width}x{height}",
         "-r", str(fps), "-i", "-",
         "-vf", "vflip,format=yuv420p",
         "-threads", "2", "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "20", "-g", "48", "-movflags", "+faststart",
         "-video_track_timescale", "24000", "-an", str(path)],
        stdin=subprocess.PIPE)


def frame_metrics(arr, prev):
    f = arr.astype(np.float32) / 255.0
    lum = f[:, :, 0] * .2126 + f[:, :, 1] * .7152 + f[:, :, 2] * .0722
    row = {
        "mean_luma": round(float(lum.mean()), 4),
        "shadow_fraction_below_0_02": round(float((lum < .02).mean()), 4),
        "highlight_fraction_above_0_98": round(float((lum > .98).mean()), 4),
        "edge_energy_proxy": round(float(np.abs(np.diff(lum, axis=0)).mean()
                                         + np.abs(np.diff(lum, axis=1)).mean()), 5),
    }
    if prev is not None:
        row["temporal_mae_vs_prev"] = round(float(np.abs(
            arr.astype(np.int16) - prev.astype(np.int16)).mean()), 4)
    return row, lum


def render_clip(stage, film, name, t0, t1, fps, width, outdir, ffmpeg,
                frozen=False, budget_tpf=None):
    h = width * 9 // 16
    n = max(1, round((t1 - t0) * fps))
    path = outdir / f"v6-{'static' if frozen else 'moving'}-{name}.mp4"
    proc = encode(width, h, fps, path, ffmpeg)
    mid = film.scene((t0 + t1) / 2.0)
    ml = mid.lenses["wide"]
    mid_lens = (np.array(ml.eye, dtype="f4"), np.array(ml.tar, dtype="f4"),
                float(ml.fov), float(ml.ratio))
    rows, prev_arr, t_start = [], None, time.monotonic()
    saved = []
    save_idx = {0, n // 2, n - 1} if frozen else {n // 2}
    try:
        prev = film.scene(max(0.0, t0 - 1 / 24))
        pf = max(0, round(prev.time * 24) - 1)
        stage.shadow(prev, pf)
        stage.frame(prev, "wide")
        for i in range(n):
            t = t0 + i / fps
            s = film.scene(t)
            if frozen:
                from geo import Lens
                s.lenses["wide"] = Lens(mid_lens[0], mid_lens[1],
                                        mid_lens[2], mid_lens[3])
            f = round(t * 24)
            stage.shadow(s, f)
            raw = stage.frame(s, "wide")
            arr = np.frombuffer(raw, dtype=np.uint8).reshape(h, width, 4)[:, :, :3]
            row, _ = frame_metrics(arr, prev_arr)
            row["frame"] = i
            row["t"] = round(t, 4)
            rows.append(row)
            prev_arr = arr.copy()
            proc.stdin.write(raw)
            if i in save_idx:
                from PIL import Image
                im = Image.frombytes("RGBA", (width, h), raw
                                     ).transpose(Image.Transpose.FLIP_TOP_BOTTOM).convert("RGB")
                pn = outdir / f"frame-{name}-{'static' if frozen else 'moving'}-{i:03d}.png"
                im.save(pn)
                saved.append(str(pn))
            if i == 1 and budget_tpf is not None:
                tpf = (time.monotonic() - t_start) / 2
                print(f"PLAN_MEASURE tpf={tpf:.2f}s clip={name} fps={fps} "
                      f"frames_total_est={tpf * n * len(WINDOWS) * (2 if STATIC else 1):.0f}",
                      flush=True)
    finally:
        proc.stdin.close()
        rc = proc.wait()
    if rc:
        raise RuntimeError(f"ffmpeg failed rc={rc} for {path}")
    wall = time.monotonic() - t_start
    summary = {
        "clip": str(path), "window": [t0, t1], "fps": fps, "width": width,
        "height": h, "frames": n, "frozen_camera": frozen,
        "wall_seconds": round(wall, 1),
        "mean_luma": round(float(np.mean([r["mean_luma"] for r in rows])), 4),
        "max_highlight_clip": round(float(max(r["highlight_fraction_above_0_98"] for r in rows)), 4),
        "max_shadow_clip": round(float(max(r["shadow_fraction_below_0_02"] for r in rows)), 4),
        "mean_edge_energy": round(float(np.mean([r["edge_energy_proxy"] for r in rows])), 5),
        "temporal_mae_mean": round(float(np.mean([r.get("temporal_mae_vs_prev", 0) for r in rows[1:]])), 4),
        "temporal_mae_max": round(float(np.max([r.get("temporal_mae_vs_prev", 0) for r in rows[1:]])), 4),
        "sample_frames": saved,
        "rows": rows,
    }
    print(f"CLIP {path} wall={wall:.0f}s frames={n}", flush=True)
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--outdir", type=Path, default=Path("out/clips"))
    p.add_argument("--width", type=int, default=960)
    p.add_argument("--fps", type=int, default=12)
    p.add_argument("--budget", type=float, default=7800.0,
                   help="wall-clock budget in seconds for all clip renders")
    a = p.parse_args()
    a.outdir.mkdir(parents=True, exist_ok=True)

    import build_film_v3 as film
    from stage_cine_v6 import Stage
    from imageio_ffmpeg import get_ffmpeg_exe
    ffmpeg = get_ffmpeg_exe()

    stage = Stage({"wide": (a.width, a.width * 9 // 16)})
    plan = {"width": a.width, "fps": a.fps, "windows": len(WINDOWS),
            "static_clips": sorted(STATIC), "budget_seconds": a.budget}
    print("PLAN " + json.dumps(plan), flush=True)

    results, report = [], {"plan": plan, "clips": []}
    for name, t0, t1 in WINDOWS:
        # Adaptive step-down: measure on the first clip, then plan the rest.
        clip = render_clip(stage, film, name, t0, t1, a.fps, a.width,
                           a.outdir, ffmpeg, budget_tpf=(a.budget if name == WINDOWS[0][0] else None))
        results.append(clip)
        report["clips"].append(clip)
        if name == WINDOWS[0][0]:
            tpf = clip["wall_seconds"] / max(1, clip["frames"])
            est = tpf * a.fps * (t1 - t0) * (len(WINDOWS) + len(STATIC))
            if est > a.budget:
                a.fps = max(8, a.fps - 4)
                plan["adjusted_fps"] = a.fps
                print(f"ADJUST fps -> {a.fps} (est {est:.0f}s > budget {a.budget:.0f}s)", flush=True)
                est = tpf * a.fps * (t1 - t0) * (len(WINDOWS) + len(STATIC))
                if est > a.budget:
                    a.width = 800
                    plan["adjusted_width"] = a.width
                    plan["adjusted_fps"] = a.fps
                    stage = Stage({"wide": (a.width, a.width * 9 // 16)})
                    print(f"ADJUST width -> {a.width}", flush=True)
            est_final = tpf * a.fps * (t1 - t0) * (len(WINDOWS) + len(STATIC))
            plan["projected_clip_seconds"] = round(est_final, 0)
            print(f"PLAN_FINAL {json.dumps(plan)}", flush=True)
        if name in STATIC:
            static = render_clip(stage, film, name, t0, t1, a.fps, a.width,
                                 a.outdir, ffmpeg, frozen=True)
            results.append(static)
            report["clips"].append(static)

    (a.outdir / "metrics.json").write_text(json.dumps(report, indent=2))
    print("CLIPS_DONE " + str(a.outdir / "metrics.json"), flush=True)


if __name__ == "__main__":
    main()
