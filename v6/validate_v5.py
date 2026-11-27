"""Dependency-light source validation for the V5 package; no GPU/context needed."""
from pathlib import Path
import ast
import hashlib
import json

ROOT = Path(__file__).resolve().parent
FILES = [
    "stage_cine_v5.py", "render_v5_stills.py",
    "stage_cine_v4.py", "stage_cine_v3.py",
    "engine/stage_cine.py",
]
for rel in FILES:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit("MISSING: " + rel)
    ast.parse(path.read_text(encoding="utf-8"), filename=rel)

engine = (ROOT / "engine/stage_cine.py").read_text(encoding="utf-8")
v4_source = (ROOT / "stage_cine_v4.py").read_text(encoding="utf-8")
checks = {
    "v4_shadow_rotation_target": "float ang=6.2831853*fract(52.9829189*fract(dot(gl_FragCoord.xy,vec2(.06711056,.00583715))));",
    "v4_grain_target": "float grit=fract(52.9829189*fract(dot(gl_FragCoord.xy+floor(time*24.)*vec2(17.23,9.7),vec2(.06711056,.00583715))))-.5;",
}
# V4 patches live in stage_cine_v4.py after its exact-string replacement,
# so the source targets must be present in the frozen engine source.
for label, target in checks.items():
    source = v4_source if label == "v4_shadow_rotation_target" else engine
    if target not in source:
        raise SystemExit("PATCH TARGET MISSING: " + label)

v5 = (ROOT / "stage_cine_v5.py").read_text(encoding="utf-8")
for required in ("world_stable_shadow_rotation", "stable_screen_grain", "importlib.reload"):
    if required not in v5:
        raise SystemExit("V5 FEATURE MISSING: " + required)

manifest_files = {}
for path in sorted(ROOT.rglob("*")):
    if path.is_file() and path.name != "V5-MANIFEST.json" and "__pycache__" not in path.parts:
        manifest_files[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
manifest = {
    "version": "v5",
    "scope": "additive temporal-stability shader pass",
    "files": manifest_files,
    "validation": "Python AST and exact patch-target checks passed; OpenGL render not run in this environment",
}
(ROOT / "V5-MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print("V5 source validation passed.")
print("Files fingerprinted:", len(manifest_files))
print("OpenGL rendering still requires the project's runtime dependencies and a working EGL/OpenGL context.")
