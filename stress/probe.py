"""EGL/software-GL probe for the V6 cinematic stage.

Boots the actual shipped V6 stage (stage_cine_v6) on the host OpenGL runtime,
renders two full frames, and reports the driver string and measured frame cost.
This validates the V6-MANIFEST "glsl_compile" and "visual_render" claims.
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
V6 = HERE.parent / "v6"
sys.path[:0] = [str(V6), str(V6 / "engine")]

import moderngl as gl

info = {}
ctx = gl.create_standalone_context(backend="egl", require=330)
info["gl_renderer"] = ctx.info.get("GL_RENDERER", "?")
info["gl_version"] = ctx.info.get("GL_VERSION", "?")
info["gl_vendor"] = ctx.info.get("GL_VENDOR", "?")
ctx.release()

import build_film_v3 as film
from stage_cine_v6 import Stage

W, H = 960, 540
stage = Stage({"wide": (W, H)})
times = [45.0, 45.5]
t0 = time.monotonic()
for i, t in enumerate(times):
    if i == 0:
        prev = film.scene(t - 1 / 24)
        stage.shadow(prev, round(t * 24) - 1)
        stage.frame(prev, "wide")
    s = film.scene(t)
    stage.shadow(s, round(t * 24))
    raw = stage.frame(s, "wide")
info["probe_frames"] = len(times)
info["scene_at_t"] = [film.scene(t).name for t in times]
info["seconds_per_frame_960x540"] = round((time.monotonic() - t0) / len(times), 3)
info["status"] = "OK"
print("PROBE " + json.dumps(info, indent=2), flush=True)
