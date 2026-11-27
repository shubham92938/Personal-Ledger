"""Offline source checks; does not require OpenGL or claim to render shaders."""
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parent
files=["stage_cine_v6.py","render_v6_stills.py","review_v6.py"]
for name in files:
    ast.parse((ROOT/name).read_text(encoding="utf-8"),filename=name)
    print("PYTHON OK",name)
s=(ROOT/"stage_cine_v6.py").read_text(encoding="utf-8")
for token in ["OLD_WATER","NEW_WATER","layered_water_volume","highlight_shoulder_and_midtone_contrast","stage_cine_v5"]:
    assert token in s, f"Missing V6 feature/guard: {token}"
assert (ROOT/"stage_cine_v5.py").exists()
assert (ROOT/"stage_cine_v4.py").exists()
assert (ROOT/"engine"/"stage_cine.py").exists()
print("SOURCE GUARDS OK")
print("OpenGL shader compilation and visual playback remain unverified until run on a supported GPU/OpenGL host.")
