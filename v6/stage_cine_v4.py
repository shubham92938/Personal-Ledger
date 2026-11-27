"""v4 stage: lighting / shading / post upgrades on top of the frozen v3 engine.

Every change is an exact-string patch of the original shaders, so if the engine
source ever changes the patch fails loudly instead of silently doing nothing.
Nothing in original-film-source is modified; this lives in the new project.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'engine'))
sys.path.insert(0, str(ROOT))
import stage_cine as sc


import os
SKIP=set(os.environ.get('V4_SKIP','').split(','))


def patch(src, old, new, label):
    if label in SKIP:
        return src
    if old not in src:
        raise RuntimeError('v4 patch target missing: ' + label)
    return src.replace(old, new)


FS, FX, FINISH = sc.FS, sc.FX, sc.FINISH

# 1. Cutaway water: was a flat unlit cyan slab. Now depth gradient, animated
#    caustic shimmer and fresnel rim so it reads as a volume of liquid.
FS = patch(FS,
    "if(K==10){float veins=.84+.16*sin(35.*W.y+sin(W.x*16.)*.7);O=vec4(c*(2.1+.49*veins)+vec3(.81,1.16,1.39),1.);return;}",
    """if(K==10){
 float r1=sin(W.y*31.+time*1.7+sin(W.x*13.+time*.9)*1.3);
 float r2=sin(W.x*23.-time*1.3+sin(W.y*17.+time*.7)*1.1);
 float caus=pow(.5+.5*r1*r2,3.);
 float dg=.55+.45*smoothstep(-.4,1.6,W.y);
 float fr=pow(1.-sat(abs(dot(n,v))),2.5);
 vec3 col=mix(vec3(.02,.27,.40),vec3(.32,.86,.96),dg)*(.88+.55*caus)+vec3(.75,.95,1.)*caus*.30+vec3(.5,.8,1.)*fr*.38;
 O=vec4(mix(col*1.2,enc(horizon),ef*.3),1.);return;}""",
    'water')

# 2. Shadows: 5 fixed taps -> 12 per-pixel-rotated taps (softer, no banding).
FS = patch(FS,
    "return .36*texture(shad,vec3(a,dep))+.16*(texture(shad,vec3(a+vec2(-.92,1.59)*t,dep))+texture(shad,vec3(a+vec2(1.78,.78)*t,dep))+texture(shad,vec3(a+vec2(.35,-1.83)*t,dep))+texture(shad,vec3(a+vec2(-1.58,-.72)*t,dep)));",
    """float ang=6.2831853*fract(52.9829189*fract(dot(gl_FragCoord.xy,vec2(.06711056,.00583715))));float cs=cos(ang),sn=sin(ang);mat2 R=mat2(cs,sn,-sn,cs);float acc=0.;
 const vec2 P[12]=vec2[12](vec2(-.326,-.406),vec2(-.840,-.074),vec2(-.696,.457),vec2(-.203,.621),vec2(.962,-.195),vec2(.473,-.480),vec2(.519,.767),vec2(.185,-.893),vec2(.507,.064),vec2(.896,.412),vec2(-.322,-.933),vec2(-.792,-.598));
 for(int i=0;i<12;i++)acc+=texture(shad,vec3(a+R*P[i]*t*1.9,dep));
 return acc/12.;""",
    'shadow')

# 3. Ambient: stronger sky-blue top light and warm ground bounce.
FS = patch(FS,
    "vec3 ambient=mix(vec3(.140,.119,.107),vec3(.18,.248,.305),sat(.5+.5*n.y));",
    "vec3 ambient=mix(vec3(.205,.150,.108),vec3(.19,.265,.335),sat(.5+.5*n.y));",
    'ambient')

# 4. Ambient occlusion: second, wider ring sampled as opposite PAIRS (min of both
#    sides) so grazing floors are not falsely darkened; stronger contact darkening.
FX = patch(FX,
    "O=vec4(color,1.-.29*min(1.,a*.222));",
    """for(int i=0;i<3;i++){float dA=z0-z(uv+x[i]*v*r*9.5),dB=z0-z(uv+x[i+3]*v*r*9.5);float m=min(dA,dB);a+=1.6*smoothstep(.013,.14,m)*(1.-smoothstep(.19,1.1,m));}
 O=vec4(color,1.-.46*min(1.,a*.16));""",
    'ao')

# 5. Bloom: add two wider rings so highlights actually glow.
FX = patch(FX,
    "color+=(hi(uv+k*1.73)+hi(uv-k*1.73))*.105;",
    "color+=(hi(uv+k*1.73)+hi(uv-k*1.73))*.105+(hi(uv+k*3.3)+hi(uv-k*3.3)+hi(uv+vec2(k.x,-k.y)*3.3)+hi(uv-vec2(k.x,-k.y)*3.3))*.06;",
    'bloom_ring')
FINISH = patch(FINISH, "c+=ef.rgb*.069;", "c+=ef.rgb*.105;", 'bloom_gain')

# 6. Grade: cool shadows / warm highlights, gentle S-curve, stronger vignette.
FINISH = patch(FINISH,
    "c=ag(c*vign);c=mix(c,vec3(Y(c)),.043);",
    """c=ag(c*mix(vign,vign*vign,.6));float lm=Y(c);c=mix(c,vec3(lm),.02);
 c=mix(c,c*vec3(.93,.99,1.08),smoothstep(.5,.0,lm)*.55);
 c=mix(c,c*vec3(1.07,1.0,.90),smoothstep(.45,1.,lm)*.5);
 c=mix(c,c*c*(3.-2.*c),.35);""",
    'grade')

sc.FS, sc.FX, sc.FINISH = FS, FX, FINISH
import stage_cine_v3 as v3
Stage = v3.Stage
