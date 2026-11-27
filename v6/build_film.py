"""Native-world 3D animation for the remaining Heron film.
All reconstructed geometry is original and interpretative. The director uses
voice-aligned edits and continually moving world-space lenses; no static-image pans.
The 6-frame-per-second picture is a work-in-progress rendering compromise.
"""
from pathlib import Path
from bisect import bisect_right
import argparse, math, os, subprocess, sys, time, json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import build_opening as B
import build_montage as U
import build_lab as L
import film_models as F
from geo import M,I,v,xform,ease,clamp
from forge import cached,bevel,tube,BRASS,PAPER,KEY,PNT,WOOD,CLOTH
from stage_fast import Stage

R=Path(__file__).resolve().parent;C=R/'.cache';S=R/'source';D=R/'deliverables'
START=992/24;END=1125.19;FPS=6

def sm(t,a,b):return ease((t-a)/(b-a))
def between(a,b,u):return v(a)+(v(b)-v(a))*ease(u)
def lin(t,a,b):return clamp((t-a)/(b-a))

# Every edit is chosen against the script's observed speech positions, in seconds.
# View names select 3D lenses aimed at the active component, not a pan on a still.
SHOTS=[
 (41.333,'coin_inside'),(49.2,'coin_lid'),(57.4,'coin_plate'),(64.0,'coin_balance'),
 (75.2,'coin_plate'),(81.2,'coin_lid'),(84.0,'coin_water'),(88.0,'coin_inside'),
 (95.7,'coin_plate'),(102.7,'coin_bin'),(109.2,'coin_inside'),(115.2,'coin_balance'),
 (120.8,'coin_plate'),(125.5,'coin_inside'),(130.8,'coin_water'),(137.8,'coin_slot'),
 (145.0,'coin_world'),(153.5,'coin_inside'),(160.0,'coin_balance'),
 (170.6,'temple_world'),(176.0,'temple_fire_world'),(181.0,'temple_world'),(188.8,'temple_world_alt'),
 (193.4,'temple_cut'),(198.0,'temple_fire'),(202.0,'temple_globe'),(211.2,'temple_globe'),
 (218.0,'temple_bucket'),(224.2,'temple_cut'),(229.0,'temple_bucket'),(235.0,'temple_doors'),
 (241.0,'temple_cut'),(249.0,'temple_world_alt'),(253.7,'temple_bucket'),(260.0,'temple_globe'),
 (266.0,'temple_bucket'),(272.0,'temple_doors'),(276.1,'temple_cut'),(283.0,'temple_globe'),
 (289.0,'temple_bucket'),(295.5,'temple_doors'),(302.0,'temple_world'),(310.0,'temple_cut'),
 (318.0,'temple_world_alt'),(322.4,'coin_inside'),(328.4,'temple_globe'),(336.0,'temple_bucket'),
 (343.5,'temple_world'),
 (352.6,'garden_world'),(361.0,'garden_bird'),(367.0,'garden_supply'),(374.0,'garden_chamber'),
 (381.0,'garden_pipe'),(388.0,'garden_bird'),(395.0,'garden_chamber'),(403.8,'garden_world'),
 (409.5,'garden_owl'),(416.0,'garden_bird'),(422.0,'garden_cut'),(429.0,'garden_siphon'),
 (435.0,'garden_chamber'),(441.0,'garden_siphon'),(449.0,'garden_bucket'),(456.0,'garden_owl'),
 (462.0,'garden_cut'),(469.0,'garden_bucket'),(476.0,'garden_owl'),(483.0,'garden_cut'),
 (490.0,'garden_bird'),(498.0,'garden_world'),(506.0,'garden_cut'),(513.0,'garden_world'),
 (518.0,'fountain_world'),(526.0,'fountain_jet'),(534.0,'fountain_world'),(542.0,'fountain_jet'),
 (551.0,'fountain_cut'),(558.0,'fountain_lower'),(564.0,'fountain_cut'),(570.0,'fountain_middle'),
 (576.0,'fountain_lower'),(583.0,'fountain_air'),(587.0,'fountain_middle'),(592.0,'fountain_cut'),
 (600.0,'fountain_jet'),(605.0,'fountain_lower'),(610.0,'fountain_jet'),(617.0,'fountain_cut'),
 (624.0,'steam_world'),(630.0,'steam_fire'),(637.0,'steam_ball'),
 (640.0,'steam_ball'),(646.0,'steam_nozzles'),(653.0,'steam_nozzles'),(660.0,'steam_ball'),
 (668.0,'steam_cut'),(676.0,'steam_cut'),(682.0,'steam_nozzles'),(689.0,'steam_ball'),
 (696.0,'steam_fire'),(704.0,'steam_world'),(711.0,'steam_ball'),(718.0,'steam_world'),
 (725.0,'steam_cut'),(732.0,'steam_ball'),(739.0,'steam_world'),(748.0,'steam_nozzles'),
 (756.0,'steam_ball'),(764.0,'steam_world'),(772.0,'steam_ball'),
 (779.8,'organ_world'),(786.0,'organ_sail'),(792.0,'organ_pipes'),(798.0,'organ_world'),
 (804.0,'organ_sail'),(810.0,'organ_cam'),(816.0,'organ_pump'),(823.0,'organ_pipes'),
 (830.0,'organ_world'),(837.0,'organ_pump'),(844.0,'organ_pipes'),(850.0,'garden_bird'),
 (855.0,'organ_cam'),(862.0,'organ_sail'),(868.0,'organ_cam'),
 (874.9,'theatre_world'),(883.0,'theatre_stage'),(888.5,'theatre_worker'),(894.0,'theatre_ship'),
 (900.0,'theatre_motor'),(906.0,'theatre_world'),(913.0,'theatre_stage'),(920.0,'theatre_motor'),
 (926.5,'theatre_weight'),(934.0,'theatre_weight'),(941.0,'theatre_motor'),(948.0,'theatre_motor'),
 (954.0,'theatre_gear'),(960.0,'theatre_worker'),(966.0,'theatre_worker'),(973.0,'theatre_gear'),
 (980.0,'theatre_doors'),(986.0,'theatre_stage'),(992.0,'theatre_doors'),(998.0,'theatre_world'),
 (1005.0,'theatre_motor'),(1012.0,'theatre_gear'),(1019.0,'theatre_stage'),(1025.0,'theatre_ship'),
 (1031.0,'theatre_storm'),(1038.0,'theatre_storm'),(1045.0,'theatre_motor'),
 (1052.1,'baghdad_world'),(1060.0,'baghdad_vessels'),(1067.0,'baghdad_world'),
 (1073.2,'coin_world'),(1080.5,'coin_inside'),(1083.0,'temple_cut'),(1088.0,'garden_world'),
 (1093.7,'theatre_world'),(1100.0,'coin_inside'),(1108.0,'temple_world'),(1113.0,'garden_bird'),
 (1117.0,'theatre_stage'),(1119.0,'coin_world'),(1122.7,'coin_inside')]
TIMES=[a for a,b in SHOTS]

# Camera locations are measured in the native geometry's world units. Each shot
# drifts toward a distinct end pose, yielding real foreground/mid/background parallax.
CAM={
'coin_inside':((.6,1.7,4.2),(0,1.21,0),30),
'coin_lid':((-.25,1.26,2.35),(-.52,.86,.22),31),
'coin_plate':((1.0,1.65,2.75),(.44,1.38,.35),30),
'coin_balance':((-.5,1.8,4.7),(0,1.22,0),27),
'coin_water':((-1.5,1.35,2.8),(-.42,.78,.92),34),
'coin_bin':((.9,1.25,2.7),(.5,.74,.30),32),
'coin_slot':((1.5,2.8,3.7),(.38,1.81,0),31),
'coin_world':((2.6,1.95,5.1),(0,1.2,0),34),
'temple_world':((4.1,2.8,8.0),(0,1.65,.3),35),
'temple_world_alt':((-3.7,2.45,7.1),(0,1.58,.3),35),
'temple_cut':((3.7,2.75,8.3),(0,1.55,0),33),
'temple_fire':((-2.9,2.7,5.5),(-1.2,2.1,.0),34),
 'temple_fire_world':((-1.4,1.9,5.0),(0,.98,2.75),34),
'temple_globe':((-2.0,1.35,4.5),(-.98,.80,.1),29),
'temple_bucket':((2.8,1.35,5.1),(.55,.75,.1),29),
'temple_doors':((3.0,2.9,5.7),(.72,2.25,-.05),32),
'garden_world':((4.2,2.7,8.2),(0,1.48,0),34),
'garden_cut':((3.2,2.0,7.1),(0,1.1,.0),32),
'garden_bird':((2.0,2.2,4.2),(.65,1.8,.0),31),
'garden_owl':((2.9,2.25,4.6),(1.25,1.85,.05),28),
'garden_supply':((-3.1,2.4,5.2),(-1.04,1.9,.0),29),
'garden_chamber':((-2.6,1.5,4.5),(-1.0,.85,.0),28),
'garden_siphon':((-.5,1.45,3.6),(-.95,.82,.25),29),
'garden_pipe':((.8,1.9,4.7),(.0,1.40,0),29),
'garden_bucket':((2.4,1.35,4.7),(.55,.75,.10),28),
'fountain_world':((3.2,2.5,6.5),(0,1.3,0),34),
'fountain_cut':((1.9,2.05,5.1),(0,1.20,0),31),
'fountain_lower':((-1.7,1.15,3.5),(0,.68,0),28),
'fountain_middle':((1.6,1.8,3.8),(0,1.55,0),28),
'fountain_air':((2.0,1.5,4.2),(.58,1.30,.0),28),
'fountain_jet':((1.4,2.65,4.2),(0,2.05,0),32),
'steam_world':((3.5,2.4,7.1),(0,1.45,0),33),
'steam_ball':((1.6,2.5,4.0),(0,2.13,0),28),
'steam_cut':((.6,2.45,3.8),(0,2.15,0),27),
'steam_nozzles':((-1.9,2.45,4.1),(0,2.15,0),29),
'steam_fire':((2.4,1.3,4.8),(0,.75,0),30),
'organ_world':((4.0,2.75,8.0),(0,1.5,0),33),
'organ_sail':((-2.8,2.6,5.3),(-.75,2.05,.05),32),
'organ_cam':((.0,2.3,4.1),(-.72,2.02,.35),29),
'organ_pump':((2.6,1.55,4.9),(.75,1.12,.15),30),
'organ_pipes':((-3.0,1.7,4.9),(-1.48,1.25,.3),30),
 'theatre_world':((3.8,2.45,7.5),(0,1.45,0),34),
 'theatre_stage':((1.4,2.1,5.0),(0,1.65,0),31),
 'theatre_worker':((1.05,1.95,4.15),(-.60,1.48,.0),28),
 'theatre_ship':((1.8,2.0,4.6),(.25,1.43,0),30),
 'theatre_motor':((2.1,1.0,4.5),(0,.62,.25),28),
 'theatre_weight':((-1.55,.90,2.35),(-1.00,.62,.28),26),
 'theatre_gear':((1.8,1.0,3.9),(.54,.62,.45),28),
 'theatre_doors':((1.5,2.3,4.8),(0,1.7,.3),32),
 'theatre_storm':((1.3,2.1,4.7),(.2,1.55,.0),31),
 'baghdad_world':((3.5,2.5,7.0),(0,1.25,.0),33),
 'baghdad_vessels':((1.6,1.8,4.2),(0,1.2,0),32),
}

@cached
def theatre_panel(side):
 g=M();d=1 if side=='L' else -1
 bevel(g,(d*.60,.64,0),(1.18,1.27,.07),'8b6041',WOOD,.014)
 for z in (-.041,.041):
  for y in (.12,.61,1.16):bevel(g,(d*.60,y,z),(1.13,.055,.03),'d4a76c',BRASS,.006)
 return g

@cached
def baghdad_backdrop():
 g=M();
 g.box((0,1.55,-2.9),(10,3.1,.35),'b69e80',PAPER)
 for x in (-3.5,-1.75,0,1.75,3.5):
  g.box((x,1.2,-2.68),(1.05,1.8,.05),'554937',WOOD)
  g.ell((x,2.10,-2.66),(.53,.54,.045),'554937',WOOD,18,9)
  for dx in (-.61,.61):bevel(g,(x+dx,1.45,-2.60),(.13,2.45,.12),'dac29e',PAPER,.018)
 bevel(g,(0,3.12,-2.7),(10.4,.14,.45),'ddc4a1',PAPER,.02)
 g.ell((0,3.22,-2.82),(1.2,.70,.60),'c6ad8d',PAPER,32,14)
 return g

@cached
def stone_table():
 g=M();bevel(g,(0,.45,0),(2.85,.90,1.16),'bda985',PAPER,.025);bevel(g,(0,.93,0),(3.05,.13,1.34),'dfcaa8',PAPER,.02)
 return g

@cached
def bar_lever():
 g=M();bevel(g,(0,0,0),(2.10,.08,.10),'b9905c',WOOD,.012);return g

def camera(t,mode,idx):
 start=SHOTS[idx][0];end=SHOTS[idx+1][0] if idx+1<len(SHOTS) else END
 eye,tar,fov=CAM[mode];eye=v(eye);tar=v(tar);u=lin(t,start,end)
 # The movement is deliberately small in a close-up, larger on the setting.
 d=.16 if any(k in mode for k in ('lid','plate','globe','bucket','chamber','siphon','nozzles','weight','gear','cam')) else .24
 sign=1 if idx%2 else -1
 endeye=eye+v((sign*d,.045,-.27 if 'world' in mode else -.16));endtar=tar+v((sign*.035,.025,0))
 return between(eye,endeye,u),between(tar,endtar,u),fov

def root_scene(t,mode,idx):
 eye,tar,fov=camera(t,mode,idx);s=B.Scene(t,f'{mode}-{idx}',eye,tar,fov)
 s.add(B.paving())
 if mode.startswith('baghdad'):
  s.add(baghdad_backdrop());s.sun=(-.55,.68,.40);s.warm=.5;s.sky='82a4b0'
 elif mode.startswith(('garden','fountain')):
  s.add(F.garden_backdrop())
  for x,z,scale in [(-4.0,-2.9,1.0),(-2.7,-4.2,.8),(2.9,-3.9,1.15),(4.5,-3.0,.9)]:s.add(F.tree(),xform((x,0,z),s=scale))
  s.sky='79a9b5';s.warm=.13;s.sun=(-.50,.72,.46)
 elif mode.startswith('steam'):
  s.add(F.workshop_backdrop());s.sky='7b8b8d';s.horizon='aaa38f';s.warm=.48;s.sun=(-.47,.70,.51)
 elif mode.startswith('organ'):
  s.add(F.terrace_backdrop());s.sky='6c9eb8';s.horizon='c9c9ae';s.sun=(-.52,.77,.39)
 elif mode.startswith('theatre'):
  s.add(F.theatre_backdrop());s.sky='6c7e85';s.horizon='a89a86';s.warm=.45;s.sun=(-.44,.75,.50)
 else:
  s.add(B.portico(),xform((0,0,-3.0)))
 for x,z,scale in [(-3.0,-1.0,.78),(3.0,-1.2,.82)]:s.add(B.planter(),xform((x,0,z),s=scale))
 return s

def coin_cycle(t):
 # Specific mechanism beats, keyed to the recording, then a recap.
 if t<75.25:return (0.,0.,False,0.)
 if t<115.2:
  # Let the falling coin reach the plate before its weight tilts the beam.
  land=sm(t,75.3,78.1);angle=-.18*sm(t,78.0,79.4)*(1-sm(t,103.0,105.0));slide=sm(t,96.8,101.7);drop=sm(t,102.0,104.1)
  return angle,slide,True,drop
 if t<137.8:
  angle=-.18*sm(t,120.1,121.5)*(1-sm(t,125.5,127.5));slide=sm(t,125.0,127.0);drop=sm(t,127.,128.5)
  return angle,slide,(t>=120.1),drop
 if t<160:return -.12,.5,True,.0
 if t<170.6:return 0.,0.,False,0.
 if 322.4<=t<328.4:return -.12,.42,True,.0
 if t>=1073:
  q=(t-1073)%19
  return (-.18*sm(q,1,3)*(1-sm(q,10,12)),sm(q,6,10),True,sm(q,10,12))
 return 0.,0.,False,0.

def make_coin(t,mode,idx):
 s=root_scene(t,mode,idx);s.add(B.pedestal());s.add(B.shell_structure())
 section=mode not in ('coin_world','coin_water','coin_slot')
 angle,slide,visible,drop=coin_cycle(t)
 if section:
  s.add(B.interior());s.add(B.lever(),xform((.03,1.27,.38),roll=angle))
  dy=-.57*math.sin(angle);s.add(B.lid(),xform((-.54,.795+dy,.46)))
  if visible:
   if 75.25<=t<80:land=sm(t,75.3,78.0)
   else:land=1.
   x=.55+.31*slide;yy=(1-land)*2.20+land*(1.38+math.sin(angle)*(x-.03))-.70*drop
   s.add(B.coin(),xform((x,yy,.38),pitch=math.pi*.5*land,roll=angle*(1-drop)))
  if angle<-.06:s.add(B.cutpipe(),I,False)
 else:
  s.add(B.front_panel());s.add(B.spigot());s.add(B.receiving_bowl())
  if mode=='coin_slot':
   y=2.35-.3*((t-137.8)%3.5)/3.5;s.add(B.coin(),xform((.50,y,.06)))
  if mode=='coin_water':
   s.add(B.stream(),B.matscale((-.42,.74,1.075),.9,.31,.9),False)
   for j in range(3):
    q=(t*2+j*.32)%1;s.add(B.drop(),xform((-.42,.71-.3*q,1.075),s=.65),False)
 return s

def temple_phase(t):
 # Hold the doors closed through the end of the 295.5–302 s close-up.
 # The model's reset to an open reference pose occurs only at the 302 s cut,
 # never as a sudden unexplained jump in the middle of a moving shot.
 if 170<=t<302:return sm(t,177.2,185.2)*(1-sm(t,260.,274.))
 if 302<=t<353:return .65
 if t>=1080:return .78
 return .6

def make_temple(t,mode,idx):
 s=root_scene(t,mode,idx);q=temple_phase(t)
 outer=(mode in ('temple_world','temple_world_alt','temple_fire_world') and (t<193.4 or 299<t<322 or t>1100))
 if outer:
  mother=I;s.add(U.temple_shell())
  s.add(U.leaf(True),xform((-.96,.52,.78),yaw=-.98*q));s.add(U.leaf(False),xform((.96,.52,.78),yaw=.98*q))
  s.add(U.altar(),xform((0,0,2.75)));s.add(U.flame_shape(),xform((0,.98,2.75),s=.85),False)
  for x in (-1.4,1.4):s.add(B.column(),xform((x,.5,.96),s=.67))
 else:
  s.add(F.cut_plinth());s.add(F.temple_pipes())
  mother=xform((.72,1.55,-.42),s=.64);s.add(U.temple_shell(),mother)
  s.add(U.leaf(True),mother@xform((-.96,.52,.78),yaw=-.98*q));s.add(U.leaf(False),mother@xform((.96,.52,.78),yaw=.98*q))
  s.add(U.altar(),xform((-1.25,1.54,0),s=.72))
  if t<260 or t>299:s.add(U.flame_shape(),xform((-1.25,2.23,0),s=.62+.08*math.sin(t*5)),False)
  s.add(F.globe_frame(),xform((-.98,.76,.14)));s.add(F.globe_water(round(7-3*q)),xform((-.98,.76,.14)),False)
  by=.42-.24*q;s.add(F.bucket(),xform((.55,by,.12),s=.76));s.add(F.clear_unit(),B.matscale((.55,by+.06,.30),.33,.31*q,.8),False)
  s.add(F.wire(),B.matscale((.55,by+.50,.52),1,max(.01,.78-by),1),False)
  s.add(F.weight_block(),xform((1.48,.35+.24*q,.32),s=.9));s.add(F.wire(),B.matscale((1.48,.43+.24*q,.42),1,.77-.24*q,1),False)
  if q>.05:
   for j in range(4):
    a=(t*.5+j*.24)%1.;s.add(F.air_bead(),xform((-1.25+.27*a,1.34,0),s=.8),False)
    b=(t*.5+j*.24)%1.;s.add(F.bead(),xform((-.77+.99*b,1.26,.20),s=.75),False)
 return s

def garden_cycle(t):
 if t<400:return .7,.25
 q=((t-400)%19)/19
 if q<.60:return q/.60,0.
 if q<.78:return 1-(q-.60)/.18,(q-.60)/.18
 return 0.,1-(q-.78)/.22

def make_garden(t,mode,idx):
 s=root_scene(t,mode,idx);s.add(F.garden_frame());s.add(F.bowl_feeder());water,turn=garden_cycle(t)
 s.add(F.clear_unit(),B.matscale((-1.01,.38,.03),1.10,.83*water,1),False)
 by=.42-.22*turn;s.add(F.bucket(),xform((.49,by,.10),s=.78));s.add(F.clear_unit(),B.matscale((.49,by+.04,.30),.34,.28*turn,.8),False)
 s.add(F.wire(),B.matscale((.49,by+.52,.52),1,.75-by,1),False)
 s.add(U.basin(),xform((-1.02,1.56,-.20),s=.60))
 for x,z in [(.35,.0),(.80,-.12)]:s.add(U.bird(False),xform((x,1.58,z),yaw=-.35+.05*math.sin(t*2),s=.78))
 s.add(U.bird(True),xform((1.35,1.57,-.12),yaw=-.85+.9*turn,s=1.20))
 s.add(B.stream(),B.matscale((-1.02,2.48,-.20),.7,.30,.7),False)
 for j in range(3):
  q=(t*1.9+j*.32)%1;s.add(B.drop(),xform((-1.02,2.44-.28*q,-.20),s=.7),False)
 # Displaced air, and therefore song, is shown during filling only; do not
 # depict continuous outflow while the siphon is draining and the birds pause.
 filling=(t<400 or ((t-400)%19)/19<.60)
 if water>.05 and filling:
  for j in range(4):
   q=(t*.65+j*.25)%1;s.add(F.air_bead(),xform((-.28+.88*q,1.75,-.08),s=.7),False)
 # The water leaving the siphon is highlighted during the drain phase.
 draining=(t>=400 and .60<=((t-400)%19)/19<.78)
 if draining:
  for j in range(4):
   q=(t*.8+j*.25)%1;s.add(F.bead(),xform((-.68+1.11*q,.25,.40),s=.65),False)
 return s

def path_point(points,phase):
 """Position a bead by distance along a polyline, preserving flow direction."""
 p=[v(a) for a in points]; lengths=[float(np.linalg.norm(b-a)) for a,b in zip(p,p[1:])]
 d=(phase%1)*sum(lengths)
 for a,b,length in zip(p,p[1:],lengths):
  if d<=length:return a+(b-a)*(d/max(length,1e-9))
  d-=length
 return p[-1]

def make_fountain(t,mode,idx):
 s=root_scene(t,mode,idx);s.add(F.fountain_frame());s.add(F.fountain_pipes());q=lin(t,570,610) if t<1000 else .4
 s.add(F.clear_unit(),B.matscale((0,.25,.04),1.02,.06+.56*q,1),False)
 s.add(F.clear_unit(),B.matscale((0,1.20,.04),1.02,.59-.52*q,1),False)
 strength=1-sm(t,604,613)
 if t<518:strength=1
 # The nozzle terminates at the bowl: the jet must start at the nozzle and
 # rise, not masquerade as a pipe descending from above it.
 if strength>.01:
  s.add(B.stream(),B.matscale((.16,2.27,.12),.65,-.48*strength,.65),False)
  for j in range(8):
   d=(t*.78+j/4)%1.;side=-1 if j%2 else 1
   x=.16+side*.33*d;y=2.27+.48*strength*(1-d*d)
   s.add(F.bead(),xform((x,y,.15),s=.72),False)
  # Colored beads follow the actual pipe paths: incoming water, trapped air,
  # and the water driven to the nozzle. Their movement is explanatory.
  routes=[([(-.15,2.12,.17),(-.80,2.12,.17),(-.80,.24,.17),(-.48,.24,.17)],F.bead),
          ([(.48,1.0,.17),(.82,1.0,.17),(.82,1.88,.17),(.46,1.88,.17)],F.air_bead),
          ([(.16,1.22,.17),(.16,2.27,.17)],F.bead)]
  for r,(pts,mesh) in enumerate(routes):
   for j in range(4):
    position=path_point(pts,t*(.16+.025*r)+j/4)
    s.add(mesh(),xform(position,s=.68),False)
 return s

def make_steam(t,mode,idx):
 s=root_scene(t,mode,idx);s.add(L.stand());s.add(L.boiler());s.add(U.flame_shape(),xform((0,.40,.15),s=.68+.08*math.sin(t*6)),False)
 angle=(t-637)*1.3
 if mode=='steam_cut':s.add(F.steam_cut(),xform((0,2.15,.06),roll=angle))
 else:s.add(L.spinner(),xform((0,2.15,0),pitch=angle))
 # Visible explanatory particles in and around the mechanism, not smoke copied from reference footage.
 for j in range(4):
  p=(t*.6+j*.25)%1;s.add(F.bead(),xform((.58,1.33+.73*p,.04),s=.7),False)
 if mode!='steam_cut':
  ca,sa=math.cos(angle),math.sin(angle)
  for sign in (-1,1):
   for j in range(3):
    p=(t*1.4+j/3)%1.;ly=sign*.59;lz=sign*(.31+.32*p)
    s.add(F.steam_puff(),xform((0,2.15+ca*ly-sa*lz,sa*ly+ca*lz),s=.65+.45*p),False)
 return s

def make_organ(t,mode,idx):
 s=root_scene(t,mode,idx);s.add(F.organ_base());a=(t-779.8)*math.tau/6
 s.add(F.wind_sail(),xform((-.75,2.10,-.05),roll=a))
 s.add(F.organ_cam(),xform((-.75,2.10,.52),roll=a))
 # Two opposed pegs: two lifts per revolution. Peg, linked bar and piston
 # all derive from the same phase, then the piston descends on release.
 lift=abs(math.sin(a))**10
 s.add(bar_lever(),xform((-.03,1.81,.45),roll=.10*lift))
 py=1.05+.075*lift
 s.add(F.piston(),xform((.72,py,.24)))
 s.add(F.air_unit(),B.matscale((.72,.56,.02),.61,py-.56,1),False)
 return s

def door_open(t):
 if t<883:return 0.
 if t<976:return sm(t,883,885)
 if t<999:return 1-sm(t,981,985)+sm(t,990,994)
 return 1.

def make_theatre(t,mode,idx):
 s=root_scene(t,mode,idx);s.add(U.theatre_shell());a=(t-875)*.85
 cam=-a*.6
 s.add(U.wheel(),xform((-.62,.61,.59),roll=a));s.add(U.wheel(),xform((.54,.62,.59),roll=cam));s.add(F.theatre_rig())
 s.add(F.theatre_weight(),xform((-1.00,.35,.31),s=.66))
 # Emphasize the slowly lowering weight in its first close view, while leaving
 # travel for the rest of the show. The block stays seated on the sand.
 q=.45*sm(t,926,950)+.55*lin(t,950,1049)
 sand_height=.32*(1-q*.6);sand_top=.39+sand_height;weight_y=sand_top+.0496
 s.add(F.sand_unit(),B.matscale((-1.00,.39,.47),.24,sand_height,.8),False)
 s.add(F.weight_block(),xform((-1.00,weight_y,.37),s=.62))
 s.add(F.wire(),B.matscale((-1.00,weight_y+.06,.50),1,max(.04,.98-weight_y-.06),1),False)
 if 926<=t<1049:
  for j in range(4):
   d=(t*1.1+j/4)%1.;s.add(F.sand_grain(),xform((-1.0,.38-.17*d,.50),s=.7),False)
 opening=door_open(t)
 # Open far enough that the leaves do not mask the little worker in close-up.
 s.add(theatre_panel('L'),xform((-1.22,1.07,.52),yaw=-opening*2.75));s.add(theatre_panel('R'),xform((1.22,1.07,.52),yaw=opening*2.75))
 x=-.66+1.25*lin(t,887,903)
 if t>930:x=-.10+.30*math.sin((t-930)*.15)
 if t>1024:x=.30+.25*math.sin((t-1024)*.35)
 s.add(U.ship(),xform((x,1.18,-.05),roll=(.10*math.sin(t*1.8) if t>1028 else 0),s=.88))
 # The visible hammer and the follower respond to the same eight-peg wheel.
 # This is a deliberately legible, schematic linkage, not a claim that all
 # dimensions of Heron's original theatre are known.
 phi=((cam-math.pi/2+math.pi/8)%(math.pi/4))-math.pi/8
 lift=sm(.28-abs(phi),0,.28)
 s.add(bar_lever(),xform((.54,.885,.68),roll=-.085*lift,s=.25))
 if t<1023:
  s.add(F.theatre_worker_rig())
  s.add(F.puppet_body(),xform((-.70,1.13,.05),s=.82))
  s.add(F.hammer_sleeve(),xform((-.70,1.13+.82*.34,.12),roll=-.32+1.05*lift,s=.82))
 if t>1025:
  for j in range(3):s.add(F.dolphin(),xform((-.86+j*.60,1.22+.08*math.sin(t*2+j),.10),roll=.16*math.sin(t*2+j),s=.58))
 if t>1030:s.add(F.thunder(),xform((.0,2.13,-.1),s=.9))
 return s

def make_baghdad(t,mode,idx):
 s=root_scene(t,mode,idx);s.add(stone_table());s.add(F.baghdad_vessels(),xform((0,1,0)));return s

def scene(t):
 idx=max(0,bisect_right(TIMES,t)-1);mode=SHOTS[idx][1]
 if mode.startswith('coin'):return make_coin(t,mode,idx)
 if mode.startswith('temple'):return make_temple(t,mode,idx)
 if mode.startswith('garden'):return make_garden(t,mode,idx)
 if mode.startswith('fountain'):return make_fountain(t,mode,idx)
 if mode.startswith('steam'):return make_steam(t,mode,idx)
 if mode.startswith('organ'):return make_organ(t,mode,idx)
 if mode.startswith('theatre'):return make_theatre(t,mode,idx)
 if mode.startswith('baghdad'):return make_baghdad(t,mode,idx)
 raise ValueError(mode)

def sheet(size):
 st=Stage({'wide':(size*16//9,size)});samples=[42,50,58,76,83,96,104,140,171,182,194,204,218,235,267,294,353,365,378,410,431,456,518,537,570,580,604,625,642,670,700,781,806,815,827,875,884,927,957,986,1033,1055,1075,1123];imgs=[]
 for j,t in enumerate(samples):
  q=scene(t);st.shadow(q,j*4);im=st.still(q,'wide');imgs.append((t,q.name,im));print('still',t,q.name,flush=True)
 w,h=480,270;out=Image.new('RGB',(w*4,math.ceil(len(imgs)/4)*(h+27)),'#172027');d=ImageDraw.Draw(out);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
 for j,(t,n,m) in enumerate(imgs):
  x=j%4*w;y=j//4*(h+27);out.paste(m.resize((w,h),Image.Resampling.LANCZOS),(x,y));d.text((x+7,y+h+4),f'{int(t//60):02}:{t%60:04.1f} · {n}',font=font,fill='#e6deca')
 out.save(C/'full-film-look.jpg',quality=90);print('SHEET_READY',flush=True)

def make_ass():
 # Shift original first-pass authored-word captions into the suffix's local clock.
 data=json.load(open(S/'longform-alignment.json'))['cues']
 header=(S/'opening-captions.ass').read_text().split('[Events]')[0]+'[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'
 def clock(t):
  cs=max(0,round(t*100));h,cs=divmod(cs,360000);m,cs=divmod(cs,6000);se,cs=divmod(cs,100);return f'{h}:{m:02d}:{se:02d}.{cs:02d}'
 import textwrap
 for x in data:
  if x['end']<=START:continue
  text='\\N'.join(textwrap.wrap(x['text'],width=43,break_long_words=False,break_on_hyphens=False))
  header+=f"Dialogue: 0,{clock(x['start']-START)},{clock(x['end']-START)},Narration,,0,0,0,,{text}\n"
 (S/'film-suffix-captions.ass').write_text(header)

def render(size,start=START,end=END,fps=FPS):
 make_ass();w=size*16//9;h=size;st=Stage({'wide':(w,h)});out=C/f'film-suffix-{h}.mp4';tmp=C/f'film-suffix-{h}.part.mp4'
 total=math.ceil((end-start)*fps);ass=S/'film-suffix-captions.ass'
 filt=f"vflip,fps=24,ass='{ass.as_posix()}',scale=in_range=full:out_range=tv:out_color_matrix=bt709,format=yuv420p"
 p=subprocess.Popen([B.FF,'-nostdin','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgba','-s',f'{w}x{h}','-r',str(fps),'-i','-','-filter_threads','1','-vf',filt,'-threads','2','-c:v','libx264','-preset','ultrafast','-crf','26','-g','48','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-video_track_timescale','24000','-an',str(tmp)],stdin=subprocess.PIPE)
 t0=time.monotonic()
 try:
  for i in range(total):
   q=scene(start+i/fps);st.shadow(q,i*2);p.stdin.write(st.frame(q,'wide'))
   if i%120==0:print('FRAME',i,'/',total,'film',round(start+i/fps,2),'shot',q.name,'fps',round((i+1)/(time.monotonic()-t0),2),'elapsed',round(time.monotonic()-t0,1),flush=True)
 finally:p.stdin.close();rc=p.wait()
 if rc:raise RuntimeError('FFmpeg failed '+str(rc))
 tmp.replace(out);print('FULL_PICTURE_READY',out,out.stat().st_size,'elapsed',round(time.monotonic()-t0,1),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--sheet',action='store_true');p.add_argument('--size',type=int,default=540);p.add_argument('--start',type=float,default=START);p.add_argument('--end',type=float,default=END);p.add_argument('--fps',type=int,default=FPS);a=p.parse_args();sheet(a.size) if a.sheet else render(a.size,a.start,a.end,a.fps)
