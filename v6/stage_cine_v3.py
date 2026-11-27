"""Native 3D cinematic stage for the seven-stage film revision.

The material is mapped to real 3D meshes; it is not a background plate. The
sky is a procedural world-direction environment, so it rotates with the lens.
"""
from pathlib import Path
import sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'engine'))
from stage_cine import Stage as CineStage, surfaces, BGV, VS, FS, FINISH
SKY=r'''#version 330
in vec2 uv;out vec4 O;
uniform vec3 zen,haze;uniform float tilt;uniform mat3 rays;
float hash21(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453123);}
float n2(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash21(i),hash21(i+vec2(1,0)),f.x),mix(hash21(i+vec2(0,1)),hash21(i+vec2(1,1)),f.x),f.y);}
void main(){
 vec3 d=normalize(rays*vec3(uv*2.-1.,1.));
 float elev=d.y+tilt*.003;
 float t=smoothstep(-.36,.28,elev);vec3 a=mix(haze,zen,t);
 vec2 p=d.xz/max(.18,d.y+.30)*.48+vec2(3.1,7.4);
 float f=.57*n2(p*2.)+.28*n2(p*4.)+.15*n2(p*8.);
 float cloud=smoothstep(.56,.76,f)*smoothstep(-.01,.23,elev);
 a=mix(a,vec3(.91,.91,.87),cloud*.16);
 O=vec4(a*a*(.82+.16*exp(-dot(uv-.5,uv-.5)*3.)),1.);
}
'''

class Stage(CineStage):
 def __init__(self,dims):
  super().__init__(dims)
  # A less clipped emissive response keeps outer fire red/orange while the
  # hotter central tongues remain golden. Geometry and light still move.
  old='if(K==11){O=vec4(c*4.+vec3(.92,.44,.12),1.);return;}'
  new='if(K==11){O=vec4(c*vec3(2.1,1.8,1.0)+vec3(.22,.065,.008),1.);return;}'
  if old not in FS:raise RuntimeError('Emissive shader changed; inspect before rendering')
  self.p=self.gl.program(vertex_shader=VS,fragment_shader=FS.replace(old,new))
  for k,i in {'mats':0,'glyph':1,'shad':2,'portrait':3}.items():self.p[k]=i
  self.p['shadowTex']=1./self.dep.size[0]
  # Install an original AI-generated stone albedo as a subtle height/albedo
  # contribution in the 3D material array. No reference-video frames are used.
  p=ROOT/'source'/'limestone-material.png'
  if p.exists():
   size,raw=surfaces();n=size[0]
   layers=np.frombuffer(raw,dtype=np.uint8).reshape(size[2],n,n,4).copy()
   im=Image.open(p).convert('L').resize((n,n),Image.Resampling.LANCZOS)
   a=np.asarray(im,dtype='f4')/255.
   # Mirror into a seamless periodic tile before making the normal derivatives.
   q=np.concatenate((a,np.fliplr(a)),axis=1)
   q=np.concatenate((q,np.flipud(q)),axis=0)
   a=np.asarray(Image.fromarray(q).resize((n,n),Image.Resampling.LANCZOS),dtype='f4')
   a=(a-a.mean())/max(.025,float(a.std()))
   stone=np.clip(.52+.075*a,0,1)
   gx=np.roll(stone,-1,1)-np.roll(stone,1,1);gy=np.roll(stone,-1,0)-np.roll(stone,1,0)
   for k,blend in ((5,.62),(9,.32),(26,.62)):
    layers[k,:,:,0]=np.uint8(np.clip((1-blend)*layers[k,:,:,0]+blend*stone*255,0,255))
    layers[k,:,:,1]=np.uint8(np.clip(layers[k,:,:,1].astype('f4')+gx*35*blend,0,255))
    layers[k,:,:,2]=np.uint8(np.clip(layers[k,:,:,2].astype('f4')+gy*35*blend,0,255))
   self.tx.write(layers.tobytes(),alignment=1);self.tx.build_mipmaps()
  self.b=self.gl.program(vertex_shader=BGV,fragment_shader=SKY)
  self.ba=self.gl.vertex_array(self.b,[])
  # Camera motion blur derives a world position from *this frame's* depth and
  # reprojects it into the previous true 3D camera. There is no frame blending.
  # Depth rejection keeps background from bleeding across a foreground edge.
  fs=FINISH.replace('uniform float focus,aperture,time;',
   'uniform float focus,aperture,time; uniform mat4 invvp,prevvp; uniform float camera_blur;')
  needle=' vec2 pp=uv-.5;float vign=1.-.33*dot(pp,pp);'
  blur=r''' if(camera_blur>.001){
   float depth=texture(dep,uv).r;
   if(depth<.99998){
    vec4 ww=invvp*vec4(uv*2.-1.,depth*2.-1.,1.);ww/=ww.w;
    vec4 prev=prevvp*ww;
    if(prev.w>.05){
     vec2 olduv=prev.xy/prev.w*.5+.5;
     vec2 motion=(uv-olduv)*camera_blur;
     float px=length(motion/inv);
     if(px>.60){
      motion*=min(1.,12./px);vec3 sum=c;float wgt=1.;
      for(int j=-2;j<=2;j++){
       if(j==0)continue;
       vec2 at=clamp(uv+motion*(float(j)*.25),vec2(.001),vec2(.999));
       float dz=abs(z(at)-d);
       if(dz<max(.035,d*.025)){sum+=color(at)*.6;wgt+=.6;}
      }
      c=mix(c,sum/wgt,.70);
     }
    }
   }
  }
'''
  if needle not in fs:raise RuntimeError('Post shader changed; inspect before rendering')
  fs=fs.replace(needle,blur+needle)
  self.post=self.gl.program(vertex_shader=BGV,fragment_shader=fs)
  self.pa=self.gl.vertex_array(self.post,[])
  self.post['col']=4;self.post['dep']=5;self.post['fx']=6
  self._previous_vp=None;self._previous_time=None;self._previous_shot=None
 def frame(self,s,name):
  lens=s.lenses[name]
  R=lens.v[:3,:3].T@np.diag([1./lens.proj[0,0],1./lens.proj[1,1],-1.])
  self.mat(self.b,'rays',R)
  adjacent=(self._previous_time is not None and self._previous_shot==s.shot and abs(s.time-self._previous_time-1/24)<.002)
  self.mat(self.post,'invvp',np.linalg.inv(lens.vp));self.mat(self.post,'prevvp',self._previous_vp if adjacent else lens.vp)
  self.post['camera_blur']=.48 if adjacent else 0.
  result=super().frame(s,name)
  self._previous_vp=lens.vp.copy();self._previous_time=s.time;self._previous_shot=s.shot
  return result
