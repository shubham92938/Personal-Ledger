"""Mechanical and practical-effect rigs for the revised 3D film.

These are explanatory reconstructions; geometry is not a measurement of a
surviving machine. Every moving piece has an explicit parent/pivot transform.
"""
import math
import numpy as np
import build_opening as B
import build_montage as U
from geo import M
from forge import cached,tube,BRASS,EMIT

@cached
def linked_lid():
 g=M()
 # Disc and a vertical hanging rod. At rest the 0.475-unit rod terminates at
 # the beam's left pivot, rather than protruding through the beam.
 tube(g,(0,0,0),(0,.06,0),.105,'ad8448',BRASS,24)
 tube(g,(0,.06,0),(0,.475,0),.014,'d6b675',BRASS,12)
 return g

@cached
def door_hinge():
 g=M()
 for y in (.15,.75,1.55,1.91):
  tube(g,(0,y-.045,0),(0,y+.045,0),.032,'b58d58',BRASS,14)
 tube(g,(0,.08,0),(0,1.98,0),.014,'d2b177',BRASS,12)
 return g

@cached
def flame(phase):
 """Animated volumetric-looking tongues built from actual 3D geometry."""
 g=M();p=math.tau*phase/32
 for j,(height,rad,dx,dz,col) in enumerate([
  (.51,.105,-.026,.000,'b4370e'),
  (.43,.090,.035,.015,'ce5b13'),
  (.32,.070,.008,.060,'d78b1d'),
 ]):
  rings=[]
  for i in range(13):
   u=i/12;yy=height*u
   sway=(.024*math.sin(p+j*1.9+u*3.0)+.014*math.sin(2*p+u*4.))*u*u
   xx=dx+sway;zz=dz+.014*math.cos(p*.8+j+u*2.5)*u
   rr=rad*max(.007,(1-u)**.68)*(.76+.24*math.sin(math.pi*u))
   rings.append([(xx+rr*math.cos(a*math.tau/12),yy,zz+rr*math.sin(a*math.tau/12)) for a in range(12)])
  for i in range(12):
   for k in range(12):g.quad(rings[i][k],rings[i][(k+1)%12],rings[i+1][(k+1)%12],rings[i+1][k],col,EMIT)
 return g

def apply(s,t):
 """Resolve parent-to-child transforms and attach practical 3D effects."""
 lever=next((x for m,x,sh in s.objects if m is B.lever()),None)
 new=[];hinges=[];fire_position=None
 for m,x,sh in s.objects:
  if m is B.lid() and lever is not None:
   # Left-hand lever pivot -> hanging rod tip; rod remains vertical under gravity.
   anchor=lever @ np.asarray((-.57,0.,.08,1.),dtype='f4')
   x=x.copy();x[:3,3]=(anchor[0],anchor[1]-.475,anchor[2]);m=linked_lid()
  if m is U.leaf(True) or m is U.leaf(False):hinges.append((door_hinge(),x,True))
  if m is U.flame_shape():
   m=flame(int(round(t*24))%32)
   fire_position=tuple(float(z) for z in (x[0,3],x[1,3]+.20,x[2,3]))
  new.append((m,x,sh))
 s.objects=new+hinges
 if fire_position:
  light=s.attributes.setdefault('light',{});light['pract']=fire_position
  light['light_power']=.72*(.94+.06*math.sin(t*7.3))
 return s
