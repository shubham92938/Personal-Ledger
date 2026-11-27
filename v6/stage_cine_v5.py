"""V5 temporal-stability pass layered on the frozen V4/V3 cinematic stage.

V5 changes only shader sampling stability. Geometry, timing, narration, captions,
and the original V3/V4 files remain untouched.
"""
from __future__ import annotations
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "engine"))
sys.path.insert(0, str(ROOT))

# Apply the exact, previously reviewed V4 shader patches first.
import stage_cine_v4  # noqa: F401
import stage_cine as sc


def patch(src: str, old: str, new: str, label: str) -> str:
    if old not in src:
        raise RuntimeError("V5 patch target missing: " + label)
    return src.replace(old, new)


# The V4 per-pixel shadow rotation changes with screen coordinates as the
# camera moves. Derive the angle from the receiver's world position instead.
# This keeps the sampling pattern attached to the surface across frames.
sc.FS = patch(
    sc.FS,
    "float ang=6.2831853*fract(52.9829189*fract(dot(gl_FragCoord.xy,vec2(.06711056,.00583715))));",
    "float ang=6.2831853*fract(.5+.5*sin(dot(W,vec3(1.73,2.17,1.31))*3.1));",
    "world_stable_shadow_rotation",
)

# Keep subtle film grain spatially stable. V4's frame-indexed grain is
# intentionally animated, but can read as fine flicker on flat gradients.
sc.FINISH = patch(
    sc.FINISH,
    "float grit=fract(52.9829189*fract(dot(gl_FragCoord.xy+floor(time*24.)*vec2(17.23,9.7),vec2(.06711056,.00583715))))-.5;",
    "float grit=fract(52.9829189*fract(dot(gl_FragCoord.xy,vec2(.06711056,.00583715))))-.5;",
    "stable_screen_grain",
)

# Reload the stage module so its shader imports resolve to the V5-updated
# engine strings. This does not modify any V3/V4 source files on disk.
import stage_cine_v3
stage_cine_v3 = importlib.reload(stage_cine_v3)
Stage = stage_cine_v3.Stage

V5_CHANGES = (
    "World-position-anchored shadow sample rotation to reduce camera-induced "
    "shadow shimmer.",
    "Spatially stable fine grain to reduce frame-to-frame noise flicker.",
)
