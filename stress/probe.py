"""EGL/software-GL probe for the V6 cinematic stage.

Boots the actual shipped V6 stage (stage_cine_v6) on the host OpenGL runtime,
renders two full frames, and reports the driver string and measured frame cost.
Writes full diagnostics to stress/out/probe-diagnostics.json so failures are
readable even where CI logs are not.
"""
from __future__ import annotations
import json
import os
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
V6 = HERE.parent / "v6"
OUT = HERE / "out"
OUT.mkdir(parents=True, exist_ok=True)
LOG = {}


def save():
    (OUT / "probe-diagnostics.json").write_text(json.dumps(LOG, indent=2))


sys.path[:0] = [str(V6), str(V6 / "engine")]

# Force headless software rendering before any GL library loads.
os.environ.setdefault("LIBGL_ALWAYS_SOFTWARE", "1")
os.environ.setdefault("GALLIUM_DRIVER", "llvmpipe")
os.environ.setdefault("EGL_PLATFORM", "surfaceless")
LOG["env"] = {k: os.environ.get(k) for k in
              ("LIBGL_ALWAYS_SOFTWARE", "GALLIUM_DRIVER", "EGL_PLATFORM", "LP_NUM_THREADS")}
print("ENV " + json.dumps(LOG["env"]), flush=True)

import moderngl as gl

LOG["moderngl_version"] = getattr(gl, "__version__", "?")


def try_create(label, **kw):
    try:
        ctx = gl.create_standalone_context(backend="egl", require=330, **kw)
        info = {k: ctx.info.get(k) for k in ("GL_RENDERER", "GL_VERSION", "GL_VENDOR")}
        ctx.release()
        LOG[label] = info
        print(f"{label} OK " + json.dumps(info), flush=True)
        return True
    except Exception as e:
        LOG[label] = {"error": repr(e), "traceback": traceback.format_exc()}
        print(f"{label} FAILED {e!r}", flush=True)
        return False


ok = try_create("egl_default")
if not ok:
    ok = try_create("egl_surfaceless")
if not ok:
    try:
        import ctypes
        ctypes.CDLL("libEGL.so.1")
        LOG["libegl_load"] = "loaded"
    except Exception as e:
        LOG["libegl_load"] = repr(e)
    ok = try_create("egl_device0", device_index=0)
if not ok:
    save()
    sys.exit(1)

# Boot the real V6 stage — it creates its own standalone context internally.
try:
    import build_film_v3 as film
    from stage_cine_v6 import Stage

    W, H = 960, 540
    stage = Stage({"wide": (W, H)})
    names, t0 = [], time.monotonic()
    for i, t in enumerate([45.0, 45.5]):
        if i == 0:
            prev = film.scene(t - 1 / 24)
            stage.shadow(prev, round(t * 24) - 1)
            stage.frame(prev, "wide")
        s = film.scene(t)
        names.append(s.name)
        stage.shadow(s, round(t * 24))
        raw = stage.frame(s, "wide")
    LOG["engine_stage"] = {
        "status": "OK",
        "scene_at_probe_times": names,
        "probe_frames": 2,
        "seconds_per_frame_960x540": round((time.monotonic() - t0) / 2, 3),
    }
    print("PROBE " + json.dumps(LOG, indent=2), flush=True)
except Exception as e:
    LOG["engine_stage"] = {"status": "FAILED", "error": repr(e),
                           "traceback": traceback.format_exc()}
    print("ENGINE STAGE FAILED", flush=True)
    save()
    sys.exit(1)
save()
