"""V6 cinematic look-development pass, layered on the reviewed V5 stage.

Adds a more dimensional water shader and a restrained highlight/contrast finish.
The V3/V4/V5 source remains unchanged. Runtime shader compilation still requires
an OpenGL 3.3 context and moderngl.
"""
from __future__ import annotations
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "engine"))
sys.path.insert(0, str(ROOT))

import stage_cine_v5  # applies V4 + V5 patches first
import stage_cine as sc


def patch(src: str, old: str, new: str, label: str) -> str:
    if old not in src:
        raise RuntimeError(f"V6 patch target missing: {label}")
    if new in src:
        return src
    return src.replace(old, new, 1)


# Water now has layered travelling waves, a finer normal field, Fresnel edge
# response, directional specular glints and depth-aware absorption. It remains
# a stylized real-time surface; it is not ray-traced refraction.
OLD_WATER = """if(K==10){
 float r1=sin(W.y*31.+time*1.7+sin(W.x*13.+time*.9)*1.3);
 float r2=sin(W.x*23.-time*1.3+sin(W.y*17.+time*.7)*1.1);
 float caus=pow(.5+.5*r1*r2,3.);
 float dg=.55+.45*smoothstep(-.4,1.6,W.y);
 float fr=pow(1.-sat(abs(dot(n,v))),2.5);
 vec3 col=mix(vec3(.02,.27,.40),vec3(.32,.86,.96),dg)*(.88+.55*caus)+vec3(.75,.95,1.)*caus*.30+vec3(.5,.8,1.)*fr*.38;
 O=vec4(mix(col*1.2,enc(horizon),ef*.3),1.);return;}"""
NEW_WATER = """if(K==10){
 float t=time*flow;
 float w1=sin(W.x*2.8+W.y*1.7+t*1.25);
 float w2=sin(W.y*5.1-W.x*1.2-t*.83);
 float w3=sin(W.x*12.0+W.y*8.0+t*1.9);
 float w4=sin(W.y*19.0-W.x*15.0-t*1.35);
 vec3 wn=normalize(n+vec3((w1*.030+w3*.009), (w2*.018+w4*.006), (w1-w2)*.012));
 float r1=sin(W.y*31.+t*1.7+sin(W.x*13.+t*.9)*1.3);
 float r2=sin(W.x*23.-t*1.3+sin(W.y*17.+t*.7)*1.1);
 float caustic=pow(max(0.,.5+.5*r1*r2),4.0);
 float depth=smoothstep(-.45,1.65,W.y);
 float ndv=sat(abs(dot(normalize(V),wn)));
 float fres=pow(1.-ndv,4.0);
 vec3 refl= mix(vec3(.025,.105,.155),vec3(.30,.52,.61),depth);
 vec3 absorb=mix(vec3(.018,.19,.27),vec3(.075,.36,.43),depth);
 vec3 halfv=normalize(normalize(sun)+normalize(V));
 float spec=pow(max(0.,dot(wn,halfv)),96.0)*(.35+.65*caustic);
 float micro=pow(max(0.,sin(W.x*47.+W.y*29.+t*2.1)*sin(W.y*39.-W.x*21.-t*1.7)),8.0);
 vec3 col=mix(absorb,refl,fres*.82)+vec3(.42,.72,.82)*fres*.32;
 col+=vec3(.68,.91,1.0)*(caustic*.13+micro*.035)+vec3(1.0,.88,.66)*spec*.72;
 col*=.91+.12*depth;
 O=vec4(mix(col,enc(horizon),ef*.27),1.);return;}"""
sc.FS = patch(sc.FS, OLD_WATER, NEW_WATER, "layered_water_volume")

# Improve highlight shoulder and local contrast without changing the existing
# V4/V5 tone-map order or lifting the blacks into grey fog.
sc.FINISH = patch(
    sc.FINISH,
    "c=sqrt(max(c,0.));",
    """// Gentle highlight compression protects bright metal, windows and water.
 c=c/(1.0+max(c-0.72,0.0)*0.22);
 // Restrained midtone contrast; near-black and near-white regions are protected.
 float mid=Y(c);float contrastMask=smoothstep(.025,.22,mid)*(1.-smoothstep(.78,.99,mid));
 c=mix(c,clamp((c-.18)*1.045+.18,0.,1.),contrastMask*.28);
 c=sqrt(max(c,0.));""",
    "highlight_shoulder_and_midtone_contrast",
)

# V5 already stabilizes the sampling and grain. Keep the V5 Stage implementation
# and expose it unchanged after the V6 shader edits.
import stage_cine_v3
stage_cine_v3 = importlib.reload(stage_cine_v3)
Stage = stage_cine_v3.Stage

V6_CHANGES = (
    "Layered water normals, travelling wave fields, Fresnel response and specular glints.",
    "Depth-aware water absorption and restrained caustic detail.",
    "Highlight shoulder and protected midtone contrast in the finishing pass.",
    "Retains V5 world-anchored shadow rotation and spatially stable grain.",
)
