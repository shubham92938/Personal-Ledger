"""EGL/software-GL probe for the V6 cinematic stage.

Boots the actual shipped V6 stage (stage_cine_v6) on the host OpenGL runtime,
renders two full frames, and reports the driver string and measured frame cost.
Diagnostics are written to stress/out/probe-diagnostics.json AND emitted as
GitHub annotations (::error) so failures are readable even where CI logs and
artifact downloads are unreachable.
"""
from __future__ import annotations
import base64
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


def annotate(label: str, payload):
    """Emit a payload as GitHub annotations (base64-chunked, API-readable)."""
    if isinstance(payload, (dict, list)):
        payload = json.dumps(payload)
    b = base64.b64encode(payload.encode()).decode()
    chunks = [b[i:i + 600] for i in range(0, len(b), 600)][:40]
    for i, ch in enumerate(chunks):
        print(f"::error title=v6diag-{label}-{i + 1}of{len(chunks)}::{ch}", flush=True)


def save():
    (OUT / "probe-diagnostics.json").write_text(json.dumps(LOG, indent=2))


def finish(ok):
    save()
    annotate("result", json.dumps({"ok": ok, **{k: v for k, v in LOG.items() if k != "raw_surfaceless"}}))
    sys.exit(0 if ok else 1)


sys.path[:0] = [str(V6), str(V6 / "engine")]

# Force headless software rendering before any GL library loads.
os.environ.setdefault("LIBGL_ALWAYS_SOFTWARE", "1")
os.environ.setdefault("GALLIUM_DRIVER", "llvmpipe")
os.environ.setdefault("EGL_PLATFORM", "surfaceless")
LOG["env"] = {k: os.environ.get(k) for k in
              ("LIBGL_ALWAYS_SOFTWARE", "GALLIUM_DRIVER", "EGL_PLATFORM", "LP_NUM_THREADS")}
print("ENV " + json.dumps(LOG["env"]), flush=True)


def raw_surfaceless_test():
    """Independent ctypes EGL test: does Mesa expose a surfaceless display at all?"""
    import ctypes
    import ctypes.util
    out = {}
    try:
        lib = ctypes.util.find_library("EGL") or "libEGL.so.1"
        out["lib"] = lib
        egl = ctypes.CDLL(lib)
        gpa = egl.eglGetProcAddress
        gpa.restype = ctypes.c_void_p
        gpa.argtypes = [ctypes.c_char_p]

        def fn(name, restype, argtypes):
            addr = gpa(name.encode())
            if not addr:
                return None
            return ctypes.CFUNCTYPE(restype, *argtypes)(addr)

        get_platform_display = fn("eglGetPlatformDisplayEXT", ctypes.c_void_p,
                                  [ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p])
        get_display = egl.eglGetDisplay
        get_display.restype = ctypes.c_void_p
        get_display.argtypes = [ctypes.c_void_p]
        initialize = egl.eglInitialize
        initialize.restype = ctypes.c_uint
        initialize.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int32),
                               ctypes.POINTER(ctypes.c_int32)]
        get_error = egl.eglGetError
        get_error.restype = ctypes.c_int32
        get_error.argtypes = []
        choose_config = egl.eglChooseConfig
        choose_config.restype = ctypes.c_uint
        choose_config.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int32),
                                  ctypes.POINTER(ctypes.c_void_p), ctypes.c_int32,
                                  ctypes.POINTER(ctypes.c_int32)]
        bind_api = egl.eglBindAPI
        bind_api.restype = ctypes.c_uint
        bind_api.argtypes = [ctypes.c_uint]
        create_context = egl.eglCreateContext
        create_context.restype = ctypes.c_void_p
        create_context.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                                   ctypes.POINTER(ctypes.c_int32)]
        make_current = egl.eglMakeCurrent
        make_current.restype = ctypes.c_uint
        make_current.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                                 ctypes.c_void_p]

        PLATFORM_SURFACELESS_MESA = 0x31DC
        dpy = None
        if get_platform_display:
            dpy = get_platform_display(PLATFORM_SURFACELESS_MESA, None, None)
            out["surfaceless_platform_available"] = bool(get_platform_display)
            out["surfaceless_dpy"] = bool(dpy)
            if not dpy:
                out["surfaceless_err"] = hex(get_error())
        if not dpy:
            dpy = get_display(None)
            out["default_dpy"] = bool(dpy)
            if not dpy:
                out["default_err"] = hex(get_error())
                return out
        major, minor = ctypes.c_int32(), ctypes.c_int32()
        if not initialize(dpy, ctypes.byref(major), ctypes.byref(minor)):
            out["initialize_err"] = hex(get_error())
            return out
        out["egl_version"] = f"{major.value}.{minor.value}"
        attribs = (ctypes.c_int32 * 13)(
            0x3033, 0x0001,  # EGL_SURFACE_TYPE, EGL_PBUFFER_BIT
            0x3022, 8,       # EGL_BLUE_SIZE
            0x3023, 8,       # EGL_GREEN_SIZE
            0x3024, 8,       # EGL_RED_SIZE
            0x3025, 8,       # EGL_DEPTH_SIZE
            0x3040, 0x0008,  # EGL_RENDERABLE_TYPE, EGL_OPENGL_BIT
            0x3038)          # EGL_NONE
        cfg = ctypes.c_void_p()
        ncfg = ctypes.c_int32()
        if not choose_config(dpy, attribs, ctypes.byref(cfg), 1, ctypes.byref(ncfg)):
            out["choose_config_err"] = hex(get_error())
            return out
        out["configs_found"] = ncfg.value
        if not bind_api(0x30A2):
            out["bind_api_err"] = hex(get_error())
            return out
        ctx_attribs = (ctypes.c_int32 * 7)(
            0x3098, 3,      # EGL_CONTEXT_MAJOR_VERSION
            0x30FB, 3,      # EGL_CONTEXT_MINOR_VERSION
            0x30FD, 0x0001, # EGL_CONTEXT_OPENGL_PROFILE_MASK, CORE
            0x3038)
        ctx = create_context(dpy, cfg, None, ctx_attribs)
        if not ctx:
            out["create_context_err"] = hex(get_error())
            return out
        if not make_current(dpy, None, None, ctx):
            out["make_current_err"] = hex(get_error())
            return out
        out["status"] = "RAW_SURFACELESS_CONTEXT_OK"
    except Exception as e:
        out["exception"] = repr(e)
        out["traceback"] = traceback.format_exc()
    return out


LOG["raw_surfaceless"] = raw_surfaceless_test()
print("RAW " + json.dumps(LOG["raw_surfaceless"]), flush=True)

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
    ok = try_create("egl_device0", device_index=0)
if not ok:
    annotate("probe", LOG)
    finish(False)

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
    print("PROBE OK " + json.dumps(LOG["engine_stage"]), flush=True)
    finish(True)
except Exception as e:
    LOG["engine_stage"] = {"status": "FAILED", "error": repr(e),
                           "traceback": traceback.format_exc()}
    print("ENGINE STAGE FAILED", flush=True)
    annotate("engine", LOG["engine_stage"])
    finish(False)
