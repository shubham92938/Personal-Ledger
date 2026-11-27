"""Reference-informed 24-Hz cinematic revision of the Heron review film.

This module is a *new version*: it does not replace the old review or Drive
files. Camera movement is world-space, not image panning. The animation and
all model dimensions remain illustrative reconstructions, not measurements of
surviving artefacts. Human playback review is required.
"""
from __future__ import annotations
import math,random
from bisect import bisect_right
import numpy as np
import build_opening as B
import build_montage as U
import build_film as F
import film_rigs_v3 as rigs
import film_sequences_v3 as seq
from geo import M,Lens,v,norm,xform,ease,clamp
from forge import cached,tube,ring,riv,bevel,BRASS,PAPER,KEY,WOOD,WALL,CLOTH

# Quicker initial dolly/orbit followed by a readable, slow tail. The target
# remains on the active mechanism; a real lens moves through a 3D scene.
def moving_lens(eye,target,u,sign=1,close=False,world=False):
 eye=v(eye);target=v(target);d=eye-target
 settle=ease(u/.52);drift=clamp(u)
 turn=(.15 if close else .29 if not world else .36)*sign*(1.0-settle)-sign*.035*drift
 # Start farther away and move toward the action, never by digital cropping.
 scale=(1.15 if close else 1.23)-(0.19 if close else 0.28)*settle-.015*drift
 co,si=math.cos(turn),math.sin(turn)
 new=v((co*d[0]+si*d[2],d[1]+.10*(1-settle),-si*d[0]+co*d[2]))*scale
 return target+new,target

BASE_CAMERA=F.camera
def chapter_camera(t,mode,idx):
 start=F.SHOTS[idx][0];end=F.SHOTS[idx+1][0] if idx+1<len(F.SHOTS) else F.END
 eye,target,fov=F.CAM[mode];u=F.lin(t,start,end);world=('world' in mode)
 # The v3 cauldron and sphere stand higher to reveal an actual hearth.
 # Follow them in world space without changing the already-approved opening.
 if mode.startswith('steam'):
  rise=seq.STEAM_RAISE if mode in ('steam_ball','steam_cut','steam_nozzles') else .20 if mode=='steam_world' else 0.
  eye=v(eye)+v((0,rise,0));target=v(target)+v((0,rise,0))
 close=any(x in mode for x in ('lid','plate','globe','bucket','chamber','siphon','nozzles','weight','gear','cam','jet','pipes'))
 # Alternate dolly arcs with opposing views; close-ups stay restrained enough
 # to preserve causal legibility while environments get a more pronounced arc.
 sign=1 if idx%2 else -1
 eye,target=moving_lens(eye,target,u,sign,close,world)
 return eye,target,fov

F.camera=chapter_camera

@cached
def chest_relief():
 """Small in-world bronze relief, not an on-screen heading or caption."""
 g=M()
 # Fine framing and a beaded circular escutcheon sharpen the hero object.
 for r,w,col in [(.20,.004,'dfbc7d'),(.115,.003,'ab844e')]:
  ring(g,(.17,1.27,.724),r,w,col,BRASS,40,2)
 for j in range(24):
  a=j*math.tau/24;r=.145
  riv(g,(.17+r*math.cos(a),1.27+r*math.sin(a),.727),(0,0,1),.006,'e3c389',BRASS)
 for x in np.linspace(-.49,.49,13):
  for y in (.735,1.725):riv(g,(float(x),y,.692),(0,0,1),.006,'d9b778',BRASS)
 return g

@cached
def floor_inlay():
 g=M()
 # Stone inlay lies on the courtyard floor and supplies an additional stable
 # foreground plane, so an orbit produces genuine spatial parallax.
 for r,w,c in [(1.53,.012,'8f7857'),(1.65,.012,'c1a579')]:ring(g,(0,.014,.12),r,w,c,PAPER,72,1)
 for j in range(32):
  a=j*math.tau/32;rr=1.59;x=rr*math.sin(a);z=.12+rr*math.cos(a)
  g.box((x,.016,z),(.045,.006,.045),'997b55' if j%2 else 'e2ccb0',PAPER)
 return g

@cached
def amphora():
 g=M();profile=[(0,.09),(.05,.14),(.16,.20),(.42,.28),(.73,.25),(.91,.17),(1.02,.12),(1.08,.16),(1.12,.16)]
 g.lathe(profile,(0,0,0),'a76246',PAPER,32)
 for y,r in [(.2,.21),(.72,.25),(1.02,.14)]:tube(g,(0,y,0),(0,y+.018,0),r,'d0a17c',PAPER,32)
 # Both curved handles join the vessel; no human hands are modelled.
 for sg in (-1,1):
  pts=[(sg*.15,.97,0),(sg*.30,.95,0),(sg*.32,.80,0),(sg*.24,.69,0)]
  for a,b in zip(pts,pts[1:]):tube(g,a,b,.025,'b87551',PAPER,10)
 return g

@cached
def courtyard_wing():
 """A physical, secondary facade for depth beyond the principal portico."""
 g=M();g.box((0,1.52,0),(30,3.04,.34),'ab9b83',WALL)
 g.box((0,.16,-.08),(30,.32,.50),'c6b79a',PAPER)
 for x in range(-14,15,3):
  # Recessed dark windows and actual raised stone trim, not a flat backdrop.
  g.box((x,1.58,-.19),(1.04,1.30,.05),'554d3e',WOOD)
  g.ell((x,2.22,-.20),(.52,.42,.035),'554d3e',WOOD,20,10)
  for dx in (-.61,.61):bevel(g,(x+dx,1.68,-.24),(.14,1.72,.16),'cdbb9b',PAPER,.02)
  for y in (.90,2.43):bevel(g,(x,y,-.25),(1.34,.12,.18),'d8c5a7',PAPER,.015)
  for dx in (-.30,0,.30):g.box((x+dx,1.58,-.245),(.035,1.24,.045),'907456',WOOD)
  for y in (1.32,1.78):g.box((x,y,-.25),(1.02,.035,.05),'957958',WOOD)
 for y in (3.04,3.16,3.26):bevel(g,(0,y,-.08),(30,.12,.68),'d8c5a6',PAPER,.02)
 g.box((0,3.36,0),(30,.12,.78),'a6674b',PAPER)
 for j in range(-65,66):tube(g,(j*.23,3.43,-.35),(j*.23,3.43,.36),.037,'bd7959',PAPER,6)
 return g

@cached
def courtyard_extension():
 g=M();g.box((0,-.115,0),(56,.16,56),'b9a78a',PAPER);return g

@cached
def textured_planter():
 """More finely modelled olive-like foliage; no people or hands."""
 g=M();g.lathe([(0,.16),(.05,.21),(.13,.28),(.35,.32),(.48,.24),(.50,.24),(.53,.28),(.57,.28),(.59,.22)],(0,0,0),'b87955',PAPER,32)
 tube(g,(0,.58,0),(0,.60,0),.21,'66563d',PAPER,24)
 rng=random.Random(144)
 for j in range(23):
  a=j*2.39996;h=rng.uniform(.80,1.20);d=rng.uniform(.24,.43);tip=v((d*math.cos(a),h,d*math.sin(a)));base=v((0,.58,0))
  tube(g,base,tip,.0055,'655e3d',WOOD,7)
  for n in (1,2,3,4):
   u=.28+n*.145;center=base+(tip-base)*u
   for side in (-1,1):
    b=a+side*(.70+rng.uniform(-.20,.25));direction=norm((math.cos(b),rng.uniform(.06,.36),math.sin(b)));across=norm((-direction[2],0,direction[0]));length=rng.uniform(.12,.19);width=rng.uniform(.025,.050)
    end=center+direction*length;mid=center+direction*length*.48+v((0,.009,0));L=mid+across*width;R=mid-across*width
    col=('435f3c','536f3d','6a7e4a','3e5a36')[(j+n+(side>0))%4]
    g.tri(center,L,end,col,CLOTH);g.tri(center,end,R,col,CLOTH)
 return g

@cached
def natural_bowl():
 g=M();x=-.42;z=1.08
 g.lathe([(.0,.12),(.04,.22),(.09,.31),(.18,.36),(.235,.37),(.25,.34),(.18,.30),(.115,.25)],(x,.31,z),'cdb186',PAPER,40)
 # More neutral reflected water; the cutaway remains diagrammatically blue.
 tube(g,(x,.424,z),(x,.430,z),.245,'82958e',KEY,40)
 bevel(g,(x,.25,z),(.84,.13,.80),'c4b293',PAPER,.026)
 return g

@cached
def water_strand(k):
 """Animated, multi-strand liquid; k is a reproducible 32-pose phase."""
 g=M();phase=k*math.tau/32;n=24
 for strand in range(3):
  pts=[]
  for i in range(n+1):
   y=-i/n;atten=math.sin(math.pi*i/n)**.7
   x=.006*math.sin(phase+11*(-y)+strand*1.7)*atten+(strand-1)*.006
   z=.005*math.cos(phase*1.23+8*(-y)+strand)*atten
   pts.append((x,y,z))
  for i,(a,b) in enumerate(zip(pts,pts[1:])):
   r=(.015 if strand==1 else .006)*(1-.18*i/n)
   tube(g,a,b,r,'b0c1c1' if strand==1 else 'd4e1df',KEY,10,cap=False)
 return g

@cached
def water_drop():
 g=M();g.ell((0,0,0),(.022,.037,.022),'c0d4d1',KEY,14,8);return g

@cached
def water_ripple():
 g=M();ring(g,(0,0,0),1,.018,'b9d8d5',KEY,40,1);return g

def polish_world(s,t):
 """Add original details; do not alter the previous version's source files."""
 out=[];hasfront=False;hasbowl=False;hasstream=False;hascabinet=False
 for m,x,sh in s.objects:
  if m is B.front_panel():hasfront=True
  if m is B.shell_structure():hascabinet=True
  if m is B.receiving_bowl():m=natural_bowl();hasbowl=True
  if m is B.planter():m=textured_planter()
  if m is B.stream():m=water_strand(int(round(t*24))%32);hasstream=True
  if m is B.drop():m=water_drop()
  out.append((m,x,sh))
 s.objects=out
 if hasfront:s.add(chest_relief())
 # The courtyard wings and ground are real, distant geometry, providing a
 # third depth plane as the camera dollies. They are excluded from other sets.
 if hascabinet or s.name in ('fire-doors','singing-garden','automatic-theatre') or s.name.startswith('temple'):
  s.add(courtyard_extension(),sh=False)
  s.add(courtyard_wing(),xform((11.8,0,0),yaw=math.pi/2))
  s.add(courtyard_wing(),xform((-11.8,0,0),yaw=-math.pi/2))
  s.add(courtyard_wing(),xform((0,0,-12.0),yaw=math.pi))
 if hascabinet:
  s.add(floor_inlay(),sh=False)
  for xx,zz,sc in [(-2.45,-1.7,.66),(2.40,-1.5,.73)]:s.add(amphora(),xform((xx,.01,zz),s=sc))
 if hasbowl and hasstream:
  for j in range(2):
   q=(t*1.15+j/2)%1.;scale=.035+.13*q
   s.add(water_ripple(),xform((-.42,.434+j*.002,1.08),s=scale),False)
 # Keep subtitles sharp: depth of field is applied in 3D before captions.
 l=s.attributes.setdefault('light',{})
 l['aperture']=13. if any(z in s.name for z in ('slot','water','lid','plate','globe','bucket','nozzles','cam','weight','gear')) else 7.
 return rigs.apply(s,t)

OPEN_BOUNDARIES=[0.,4.83,6.75,10.75,14.17,18.83,616/24]
MONTAGE_BOUNDARIES=[616/24,616/24+5.35,616/24+8.45,992/24]

def scene(t):
 if t<616/24:
  f=min(615,max(0,int(round(t*24))));s=B.make_scene(f)
  k=max(0,bisect_right(OPEN_BOUNDARIES,t)-1);start,end=OPEN_BOUNDARIES[k:k+2]
  u=clamp((t-start)/(end-start));lens=s.lenses['wide'];eye,target=moving_lens(lens.eye,lens.tar,u,1 if k%2 else -1,k in (1,2),k==0)
  s.lenses['wide']=Lens(eye,target,lens.fov,16/9);s.lenses['short']=s.lenses['wide']
 elif t<992/24:
  f=min(375,max(0,int(round((t-616/24)*24))));s=U.scene(f)
  k=max(0,bisect_right(MONTAGE_BOUNDARIES,t)-1);start,end=MONTAGE_BOUNDARIES[k:k+2]
  u=clamp((t-start)/(end-start));lens=s.lenses['wide'];eye,target=moving_lens(lens.eye,lens.tar,u,1 if k%2 else -1,False,True)
  s.lenses['wide']=Lens(eye,target,lens.fov,16/9);s.lenses['short']=s.lenses['wide']
  s.time=t
 else:
  idx=max(0,bisect_right(F.TIMES,t)-1);mode=F.SHOTS[idx][1]
  # Only the new v3 revision gets these voice-aligned state controls. The
  # already uploaded and earlier review pictures remain untouched.
  if mode.startswith('temple'):s=seq.temple(t,mode,idx)
  elif mode.startswith('garden'):s=seq.garden(t,mode,idx)
  elif mode.startswith('fountain'):s=seq.fountain(t,mode,idx)
  elif mode.startswith('steam'):s=seq.steam(t,mode,idx)
  elif mode.startswith('theatre'):s=seq.theatre(t,mode,idx)
  else:s=F.scene(t)
 return polish_world(s,t)
