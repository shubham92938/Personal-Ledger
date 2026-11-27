"""Original explanatory three-dimensional mechanism models.
Their dimensions, materials and visible cuts are modern didactic reconstructions.
"""
from __future__ import annotations
import math
import numpy as np
import build_opening as B
import build_montage as U
from geo import M,I,v,xform
from forge import cached,bevel,tube,ring,riv,BRASS,PAPER,KEY,PNT,WOOD,CLOTH,EMIT,WALL

@cached
def clear_unit():
 g=M();g.box((0,.5,0),(1,1,.10),'58b1bf',KEY);return g
@cached
def sand_unit():
 g=M();g.box((0,.5,0),(1,1,.10),'c3a36a',PAPER);return g
@cached
def bead():
 g=M();g.ell((0,0,0),(.028,.028,.028),'c4f0ec',KEY,8,4);return g
@cached
def air_bead():
 g=M();g.ell((0,0,0),(.035,.035,.035),'f3c677',EMIT,8,4);return g
@cached
def wire():
 g=M();tube(g,(0,0,0),(0,1,0),.014,'c4a975',WOOD,8);return g
@cached
def pipe_unit():
 g=M();tube(g,(0,0,0),(0,1,0),.023,'a78355',BRASS,12);return g

@cached
def cut_plinth():
 g=M();bevel(g,(0,.08,0),(4.7,.16,1.78),'d0bd9f',PAPER,.025)
 bevel(g,(0,1.48,0),(4.35,.12,1.5),'c8b595',PAPER,.02)
 # Face is open; rear masonry, floor and thin uprights imply an excavation.
 g.box((0,.76,-.70),(4.25,1.34,.08),'71624d',WALL)
 for x in (-2.08,2.08):bevel(g,(x,.76,0),(.16,1.3,1.42),'c2ad8b',PAPER,.018)
 return g

@cached
def globe_frame():
 g=M();g.ell((0,0,-.07),(.52,.52,.08),'65533d',BRASS,26,12)
 ring(g,(0,0,.04),.52,.045,'c49e64',BRASS,32,2)
 ring(g,(0,0,.09),.45,.012,'e0bb7d',BRASS,32,2)
 for a in range(0,360,45):
  q=math.radians(a);riv(g,(.52*math.cos(q),.52*math.sin(q),.10),(0,0,1),.021,'e4c38a',BRASS)
 return g

@cached
def globe_water(q):
 # Circular blue segment for a transparent explanatory cut face. Quantized for caching.
 level=max(0,min(10,int(q)))/10.;r=.43;cut=-r+2*r*level
 pts=[(r*math.cos(j*math.tau/48),r*math.sin(j*math.tau/48)) for j in range(48)];out=[]
 for A,Bb in zip(pts,pts[1:]+pts[:1]):
  ina=A[1]<=cut;inb=Bb[1]<=cut
  if ina:out.append(A)
  if ina!=inb:
   f=(cut-A[1])/(Bb[1]-A[1]);out.append((A[0]+f*(Bb[0]-A[0]),cut))
 g=M()
 if len(out)>=3:
  cx=sum(x for x,y in out)/len(out);cy=sum(y for x,y in out)/len(out)
  for a,b in zip(out,out[1:]+out[:1]):g.tri((cx,cy,.095),(a[0],a[1],.095),(b[0],b[1],.095),'64c4cb',KEY,((0,0,1),)*3)
 return g

@cached
def bucket():
 g=M();
 for x in (-.27,.27):bevel(g,(x,.25,0),(.055,.50,.45),'a88456',WOOD,.008)
 bevel(g,(0,.025,0),(.58,.05,.48),'a88456',WOOD,.008);g.box((0,.25,-.205),(.50,.43,.035),'6b4e37',WOOD)
 for y in (.08,.40):bevel(g,(0,y,.235),(.56,.038,.025),'d5b77c',BRASS,.006)
 tube(g,(-.23,.50,0),(0,.66,0),.015,'d2b57a',BRASS,8);tube(g,(0,.66,0),(.23,.50,0),.015,'d2b57a',BRASS,8)
 return g

@cached
def temple_pipes():
 g=M();
 def path(pts,color='a18054',r=.043):
  for a,b in zip(pts,pts[1:]):tube(g,a,b,r,color,BRASS,12)
 # Warmed air line from the hearth to the crown of the pressure globe.
 path([(-1.25,1.53,0),(-1.25,1.34,0),(-.98,1.34,0),(-.98,1.22,0)],'c49b60')
 # Outlet takes water up from the globe, then downward into suspended bucket.
 path([(-.77,.38,.16),(-.77,1.26,.16),(-.22,1.26,.16),(-.22,1.03,.16),(.55,1.03,.16)],'ad8b57')
 # Ropes/pulleys carry motion to the doors above; direction is illustrative.
 for x in (.57,1.48):
  ring(g,(x,1.28,.40),.13,.025,'d6b779',BRASS,18,2)
  tube(g,(x,1.14,.40),(x,1.42,.40),.012,'e2c690',WOOD,8)
 tube(g,(.57,1.39,.40),(1.48,1.39,.40),.014,'dfc18b',WOOD,8)
 return g

@cached
def garden_frame():
 g=M();
 bevel(g,(0,.08,0),(4.55,.16,1.77),'d0bd9f',PAPER,.025)
 bevel(g,(0,1.52,0),(4.18,.10,1.44),'cdb999',PAPER,.02)
 g.box((0,.80,-.66),(4.0,1.36,.06),'6d604c',WALL)
 for x in (-1.98,1.98):bevel(g,(x,.78,0),(.15,1.31,1.30),'c6b18f',PAPER,.02)
 # Sealed first vessel, side walls and rear panel; front removed for clarity.
 for x in (-1.62,-.40):bevel(g,(x,.83,0),(.075,1.02,.75),'c3a469',BRASS,.01)
 for y in (.33,1.34):bevel(g,(-1.01,y,0),(1.28,.07,.75),'c7a872',BRASS,.01)
 g.box((-1.01,.83,-.34),(1.2,.94,.04),'5f574a',WOOD)
 # Bent siphon. Right-hand leg reaches below the upper chamber into the bucket.
 pts=[(-1.31,.39,.35),(-1.31,1.17,.35),(-.68,1.17,.35),(-.68,.25,.35),(.43,.25,.35),(.43,.68,.35)]
 for a,b in zip(pts,pts[1:]):tube(g,a,b,.040,'d2aa70',BRASS,12)
 # Separate narrow air route climbs to the bird pipe.
 pts=[(-.52,1.24,-.1),(-.28,1.24,-.1),(-.28,1.75,-.1),(.61,1.75,-.1),(.61,1.98,-.1)]
 for a,b in zip(pts,pts[1:]):tube(g,a,b,.032,'dfbf83',BRASS,12)
 # Owl linkage and high wheel.
 ring(g,(1.47,1.32,.45),.13,.025,'d6b779',BRASS,18,2)
 tube(g,(1.47,1.19,.45),(1.47,.44,.45),.013,'e1c693',WOOD,8)
 return g

@cached
def bowl_feeder():
 g=M();
 # A visible supply into the chamber: only the working principle is asserted.
 tube(g,(-1.04,1.55,0),(-1.04,2.29,0),.040,'c3a06d',BRASS,12)
 g.lathe([(0,.12),(.09,.22),(.21,.31),(.25,.31)],(-1.04,2.28,0),'d3be95',PAPER,24)
 return g

@cached
def fountain_frame():
 g=M();
 bevel(g,(0,.08,0),(2.9,.16,1.60),'d2bea1',PAPER,.025)
 for y in (.62,1.57):
  for x in (-.56,.56):bevel(g,(x,y,0),(.08,.82,.70),'b89960',BRASS,.01)
  for yy in (y-.40,y+.40):bevel(g,(0,yy,0),(1.16,.075,.72),'cfad76',BRASS,.012)
  g.box((0,y,-.31),(1.08,.72,.035),'5c5443',WOOD)
  for x in (-.56,.56):
   for yy in (y-.25,y+.25):riv(g,(x,yy,.38),(0,0,1),.018,'e3c289',BRASS)
 g.lathe([(0,.18),(.06,.28),(.12,.48),(.18,.62),(.22,.65),(.25,.59),(.16,.52)],(0,2.06,0),'d0b98e',PAPER,30)
 tube(g,(0,2.23,0),(0,2.25,0),.49,'60aeb4',KEY,30)
 return g

@cached
def fountain_pipes():
 g=M()
 routes=[([(-.15,2.12,.1),(-.80,2.12,.1),(-.80,.24,.1),(-.48,.24,.1)],'62bbc2'),
         ([(.48,1.0,.1),(.82,1.0,.1),(.82,1.88,.1),(.46,1.88,.1)],'efc274'),
         ([(.16,1.22,.1),(.16,2.27,.1)],'8ddde0')]
 for pts,col in routes:
  for a,b in zip(pts,pts[1:]):
   tube(g,a,b,.043,'ae8b58',BRASS,12)
   tube(g,(a[0],a[1],a[2]+.043),(b[0],b[1],b[2]+.043),.012,col,KEY,8)
 return g

@cached
def steam_cut():
 g=M();g.ell((0,0,-.10),(.45,.45,.08),'66594b',BRASS,26,12);ring(g,(0,0,.00),.45,.035,'d8b27c',BRASS,32,2)
 g.ell((0,0,.04),(.36,.36,.03),'98d4df',KEY,24,12)
 for sign in (-1,1):
  tube(g,(0,sign*.40,0),(0,sign*.60,0),.046,'d7b47e',BRASS,12)
  tube(g,(0,sign*.60,0),(0,sign*.60,sign*.27),.046,'d7b47e',BRASS,12)
 return g

@cached
def organ_base():
 g=M();bevel(g,(0,.08,0),(4.4,.16,1.7),'cab597',PAPER,.025)
 for x in (-1.5,1.3):
  for z in (-.42,.42):bevel(g,(x,1.25,z),(.11,2.4,.11),'936d47',WOOD,.015)
  bevel(g,(x,2.45,0),(.15,.12,1.0),'ad8758',WOOD,.015)
 for y in (.25,1.0,2.33):bevel(g,(-.1,y,-.38),(2.9,.10,.10),'a27b51',WOOD,.01)
 # Pump housing is open faced; an illustrated blue chamber represents air.
 bevel(g,(.72,.49,.2),(.76,.13,.73),'8e6642',WOOD,.015)
 for x in (.36,1.08):bevel(g,(x,.90,.2),(.09,.83,.73),'af8a59',WOOD,.012)
 g.box((.72,.90,-.12),(.64,.75,.035),'655843',WOOD)
 # Organ pipes: varied lengths, terminating in a common air box.
 bevel(g,(-1.42,.67,.30),(.83,.22,.32),'a67d4a',WOOD,.018)
 for j in range(5):
  x=-1.73+j*.16;h=.52+.15*j
  tube(g,(x,.76,.30),(x,.76+h,.30),.052,'cfad70',BRASS,12)
  tube(g,(x,.76+h,.30),(x,.78+h,.30),.063,'e2c58a',BRASS,12)
 return g

@cached
def wind_sail():
 g=M();
 for j in range(6):
  a=j*math.tau/6;ca,sa=math.cos(a),math.sin(a)
  def pt(x,y):return (ca*x-sa*y,sa*x+ca*y,0)
  tube(g,pt(.10,0),pt(1.0,0),.022,'9c7a51',WOOD,8)
  g.quad(pt(.24,.02),pt(.90,.02),pt(.96,.28),pt(.32,.19),'e3d0a7',CLOTH)
  tube(g,pt(.30,.18),pt(.96,.28),.012,'b49368',WOOD,6)
 return g

@cached
def organ_cam():
 g=M();
 ring(g,(0,0,0),.34,.035,'bc985f',BRASS,24,2)
 for a in (0,math.pi):
  tube(g,(0,0,0),(.32*math.cos(a),.32*math.sin(a),0),.023,'c7a66d',BRASS,10)
  tube(g,(.32*math.cos(a),.32*math.sin(a),.02),(.32*math.cos(a),.32*math.sin(a),.18),.045,'e3c188',BRASS,12)
 return g

@cached
def piston():
 g=M();bevel(g,(0,0,0),(.62,.075,.61),'b8945b',WOOD,.01);tube(g,(0,0,0),(0,.76,0),.035,'dfc183',BRASS,12);return g

@cached
def theatre_weight():
 g=M();
 # Raised open-faced sand cylinder and weight make the motor visible beneath the stage.
 for x in (-.22,.22):bevel(g,(x,.39,0),(.055,.75,.37),'b79764',WOOD,.009)
 for y in (.05,.76):bevel(g,(0,y,0),(.46,.06,.40),'b89a68',WOOD,.009)
 g.box((0,.4,-.18),(.39,.68,.03),'4b3e31',WOOD)
 return g
@cached
def weight_block():
 g=M();bevel(g,(0,0,0),(.34,.16,.31),'aa9981',PAPER,.018);tube(g,(0,.07,0),(0,.20,0),.014,'d5b77e',WOOD,8);return g
@cached
def puppet_body():
 g=M();g.ell((0,.28,0),(.08,.14,.06),'d5b896',CLOTH,12,8);g.ell((0,.48,0),(.07,.08,.065),'bc9876',PAPER,12,8)
 for x in (-.04,.04):tube(g,(x,.04,0),(x,.19,0),.025,'a2866c',CLOTH,8)
 return g
@cached
def hammer_sleeve():
 g=M();tube(g,(0,0,0),(.14,.0,0),.035,'ccb394',CLOTH,8)
 # The hammer is fixed to the sleeve as a stage prop; there is intentionally no hand.
 tube(g,(.12,0,0),(.27,0,0),.014,'8d6844',WOOD,8);bevel(g,(.28,0,0),(.09,.10,.08),'8c8980',BRASS,.008);return g
@cached
def dolphin():
 g=M();g.ell((0,0,0),(.20,.07,.055),'91afb0',PNT,14,8);g.ell((.19,.012,0),(.10,.045,.04),'9fbaba',PNT,12,6)
 g.tri((-.14,0,0),(-.27,.09,0),(-.25,-.07,0),'8ea9aa',PNT)
 g.tri((-.03,.03,0),(.02,.12,0),(.07,.04,0),'8ea9aa',PNT)
 return g
@cached
def thunder():
 g=M()
 for x,y,z,s in [(-.45,0,0,.22),(-.15,.08,0,.28),(.2,.02,0,.27),(.46,-.04,0,.20)]:g.ell((x,y,z),(s,s*.6,s*.6),'596b78',PAPER,12,7)
 return g

@cached
def baghdad_vessels():
 g=M();
 # Small display of vessels; forms are illustrative, not specific archaeological finds.
 for x,c in [(-.75,'a17a4b'),(0,'bc8b55'),(.76,'a58059')]:
  prof=[(0,.14),(.08,.22),(.21,.29),(.50,.31),(.67,.24),(.79,.12),(.83,.15)]
  g.lathe(prof,(x,0,0),c,BRASS,24)
  for y in (.18,.55):tube(g,(x,y,0),(x,y+.018,0),.292,'d8b177',BRASS,24)
 return g

@cached
def tree():
 g=M();tube(g,(0,0,0),(0,2.1,0),.09,'745d40',WOOD,14)
 for j,(h,w) in enumerate([(1.15,.38),(1.52,.46),(1.93,.40),(2.26,.33),(2.53,.20)]):
  g.ell((0,h,0),(w,w*.78,w*.68),('536d48','687c52','4e704a','728557','526a46')[j],CLOTH,12,7)
 return g

@cached
def garden_backdrop():
 g=M();
 # Low terrace wall and columns leave the sky visible; the trees are separate meshes.
 bevel(g,(0,.55,-3.55),(13,1.1,.35),'b3a183',PAPER,.018)
 for y in (.11,1.12):bevel(g,(0,y,-3.36),(13.2,.12,.28),'d1bea1',PAPER,.02)
 for x in (-5.2,-3.9,-2.6,2.6,3.9,5.2):
  bevel(g,(x,1.43,-3.36),(.14,.55,.18),'e1d0af',PAPER,.012)
  bevel(g,(x,1.72,-3.36),(.28,.10,.30),'dfccaa',PAPER,.015)
  g.ell((x,1.88,-3.36),(.12,.12,.12),'b8a17d',PAPER,10,6)
 return g

@cached
def workshop_backdrop():
 g=M();
 g.box((0,1.95,-4.35),(13,3.9,.42),'756651',WALL)
 for x in (-4.8,-1.7,1.6,4.8):
  g.box((x,2.1,-4.1),(1.35,1.9,.05),'38413d',WOOD)
  g.ell((x,3.04,-4.08),(.68,.67,.04),'38413d',WOOD,16,8)
  for dx in (-.74,.74):bevel(g,(x+dx,2.0,-4.02),(.12,2.25,.14),'bbab8b',PAPER,.01)
  for y in (1.18,2.10,2.96):bevel(g,(x,y,-3.99),(1.44,.07,.14),'9c8463',WOOD,.008)
  for j in range(4):
   xx=x-.48+j*.32;h=.15+.09*(j%3)
   g.lathe([(0,.07),(.04,.10),(h,.11),(h+.05,.05)],(xx,1.23,-3.95),'b38e58',BRASS,14)
 for x in (-6,-3,0,3,6):bevel(g,(x,2.0,-3.85),(.16,3.85,.24),'c8b394',PAPER,.018)
 bevel(g,(0,3.84,-3.75),(13,.18,.30),'a88f6c',WOOD,.02)
 return g

@cached
def terrace_backdrop():
 g=M();
 # An open terrace exposes the wind machine to sky rather than enclosing it indoors.
 bevel(g,(0,.52,-3.55),(13,1.02,.38),'b6a486',PAPER,.02)
 for x in (-5,-3.5,-2,2,3.5,5):
  bevel(g,(x,1.03,-3.45),(.28,.12,.40),'d2bea0',PAPER,.015)
  bevel(g,(x,1.42,-3.45),(.13,.70,.16),'cbb797',PAPER,.012)
  g.ell((x,1.82,-3.45),(.13,.13,.13),'d2bea0',PAPER,10,6)
 return g

@cached
def theatre_backdrop():
 g=M();g.box((0,1.9,-4.2),(13,3.8,.40),'78624c',WALL)
 for x in (-5.1,-2.8,2.8,5.1):
  g.box((x,1.82,-3.96),(1.18,2.30,.05),'453e35',WOOD)
  g.ell((x,2.97,-3.94),(.59,.59,.04),'453e35',WOOD,16,8)
  for dx in (-.65,.65):bevel(g,(x+dx,1.85,-3.90),(.12,2.58,.16),'b49c7a',PAPER,.014)
 for x in (-6,-3.8,0,3.8,6):bevel(g,(x,1.9,-3.75),(.19,3.65,.24),'bca786',PAPER,.02)
 for y in (3.45,3.68):bevel(g,(0,y,-3.71),(13,.12,.35),'cbb38e',PAPER,.02)
 # Warm sconces imply practical light sources, distinct from outdoor shots.
 for x in (-4.7,4.7):
  tube(g,(x,1.7,-3.7),(x,2.1,-3.7),.045,'c5a06c',BRASS,10)
  g.ell((x,2.17,-3.7),(.10,.17,.07),'e4ad51',EMIT,10,6)
 return g

@cached
def air_unit():
 g=M();g.box((0,.5,0),(1,1,.10),'e7bf79',PNT);return g

@cached
def steam_puff():
 g=M();g.ell((0,0,0),(.045,.04,.045),'d9e5e0',PAPER,10,6);return g

@cached
def sand_grain():
 g=M();g.ell((0,0,0),(.013,.018,.013),'d6bc82',PAPER,8,5);return g

@cached
def theatre_rig():
 g=M()
 # Rope and axle runs are kept visible across the open machinery bay.
 for x in (-.62,.54):
  tube(g,(x,.61,.18),(x,.61,.63),.035,'a68253',WOOD,10)
  tube(g,(x,.82,.54),(x,1.01,.54),.014,'d7c293',WOOD,8)
 tube(g,(-1.0,.89,.52),(-.62,.89,.52),.014,'d7c293',WOOD,8)
 tube(g,(-.62,.89,.52),(-.62,.61,.52),.014,'d7c293',WOOD,8)
 return g

@cached
def theatre_worker_rig():
 # The schematic cord appears only during the worker demonstration; it does
 # not remain floating across the later sea scene after the worker vanishes.
 g=M()
 tube(g,(.54,.90,.52),(.54,1.08,.12),.010,'d7c293',WOOD,8)
 tube(g,(.54,1.08,.12),(-.70,1.08,.12),.010,'d7c293',WOOD,8)
 tube(g,(-.70,1.08,.12),(-.70,1.39,.12),.010,'d7c293',WOOD,8)
 return g
