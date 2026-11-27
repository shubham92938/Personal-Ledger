"""Voice-aligned mechanical staging for the full v3 revision.

This module affects only new v3 renders. It keeps separate controls for the
physical effects so a spoken explanation does not show all steps happening at
once. These illustrative reconstructions still require human playback review.
"""
from __future__ import annotations
import math
import build_opening as B
import build_montage as U
import build_film as F
from geo import M,I,xform,clamp
from forge import cached,bevel,tube,KEY,PAPER,BRASS,WOOD

sm=F.sm

@cached
def globe_water_256(level):
 """Finely quantized circular liquid surface for the explanatory cut face."""
 level=max(0,min(256,int(level)))/256.;r=.43;cut=-r+2*r*level
 pts=[(r*math.cos(j*math.tau/48),r*math.sin(j*math.tau/48)) for j in range(48)]
 out=[]
 for a,b in zip(pts,pts[1:]+pts[:1]):
  ia=a[1]<=cut;ib=b[1]<=cut
  if ia:out.append(a)
  if ia!=ib:
   f=(cut-a[1])/(b[1]-a[1]);out.append((a[0]+f*(b[0]-a[0]),cut))
 g=M()
 if len(out)>2:
  x=sum(p[0] for p in out)/len(out);y=sum(p[1] for p in out)/len(out)
  for a,b in zip(out,out[1:]+out[:1]):
   g.tri((x,y,.095),(a[0],a[1],.095),(b[0],b[1],.095),'64c4cb',KEY,((0,0,1),)*3)
 return g

def temple_state(t):
 """Return flame, transferred-water amount and door/weight displacement."""
 if t<193.4:
  # The first exterior demonstration: no fire until the narrator lights it.
  fire=sm(t,176.1,177.7);water=sm(t,178.2,183.5);door=sm(t,179.3,184.7)
 elif t<259.8:
  # On the explanatory cut at 193.4, reset and replay the hidden chain:
  # fire/air, water transfer, *then* bucket/door motion.
  fire=1.;water=sm(t,214.,224.);door=sm(t,224.2,239.4)
 elif t<276.1:
  fire=1-sm(t,259.8,261.3);water=1-sm(t,263.2,268.5);door=1-sm(t,269.,275.8)
 elif t<302.:
  # The narration explicitly recaps the exchange. Relight and replay it.
  fire=sm(t,278.7,281.4);water=sm(t,283.2,287.4);door=sm(t,287.8,290.6)
 elif t<353.:
  fire=1.;water=1.;door=1.
 else:
  # Later return to the already-operating mechanism.
  fire=1.;water=.78;door=.78
 return fire,water,door

def temple(t,mode,idx):
 s=F.root_scene(t,mode,idx);fire,water,door=temple_state(t)
 outer=(mode in ('temple_world','temple_world_alt','temple_fire_world') and (t<193.4 or 299<t<322 or t>1100))
 if outer:
  s.add(U.temple_shell())
  s.add(U.leaf(True),xform((-.96,.52,.78),yaw=-.98*door))
  s.add(U.leaf(False),xform((.96,.52,.78),yaw=.98*door))
  s.add(U.altar(),xform((0,0,2.75)))
  if fire>.015:s.add(U.flame_shape(),xform((0,.98,2.75),s=.85*max(.20,fire)),False)
  for x in (-1.4,1.4):s.add(B.column(),xform((x,.5,.96),s=.67))
 else:
  s.add(F.F.cut_plinth());s.add(F.F.temple_pipes())
  mother=xform((.72,1.55,-.42),s=.64);s.add(U.temple_shell(),mother)
  s.add(U.leaf(True),mother@xform((-.96,.52,.78),yaw=-.98*door))
  s.add(U.leaf(False),mother@xform((.96,.52,.78),yaw=.98*door))
  s.add(U.altar(),xform((-1.25,1.54,0),s=.72))
  if fire>.015:s.add(U.flame_shape(),xform((-1.25,2.23,0),s=(.62+.08*math.sin(t*5))*max(.20,fire)),False)
  s.add(F.F.globe_frame(),xform((-.98,.76,.14)))
  level=round(256*(.70-.30*water));s.add(globe_water_256(level),xform((-.98,.76,.14)),False)
  # The bucket may fill while seated; its downward movement and the counter-
  # weight/pivots then respond together. On cooling, the reverse occurs.
  by=.42-.24*door;s.add(F.F.bucket(),xform((.55,by,.12),s=.76))
  if water>.002:s.add(F.F.clear_unit(),B.matscale((.55,by+.06,.30),.33,.31*water,.8),False)
  s.add(F.F.wire(),B.matscale((.55,by+.50,.52),1,max(.01,.78-by),1),False)
  s.add(F.F.weight_block(),xform((1.48,.35+.24*door,.32),s=.9))
  s.add(F.F.wire(),B.matscale((1.48,.43+.24*door,.42),1,.77-.24*door,1),False)
  airpath=[(-1.25,1.53,0),(-1.25,1.34,0),(-.98,1.34,0),(-.98,1.22,0)]
  wetpath=[(-.77,.38,.20),(-.77,1.26,.20),(-.22,1.26,.20),(-.22,1.03,.20),(.55,1.03,.20)]
  if (205<=t<224.2) or (281.4<=t<287.4):
   for j in range(4):s.add(F.F.air_bead(),xform(F.path_point(airpath,t*.26+j/4),s=.7),False)
  outward=(214<=t<224.) or (283.2<=t<287.4)
  returning=263.2<=t<268.5
  if outward or returning:
   path=wetpath if outward else list(reversed(wetpath))
   for j in range(4):s.add(F.F.bead(),xform(F.path_point(path,t*.22+j/4),s=.72),False)
 return s

def garden_state(t):
 """Upper water, owl turn, flow direction and separate bucket fill."""
 if t<397.:
  water=.35+.35*sm(t,372.,386.);turn=0.;bucket=0.;filling=True;draining=False
 elif t<400.:
  u=sm(t,397.,400.);water=.70*(1-u);turn=.20*math.sin(math.pi*u);bucket=turn;filling=False;draining=True
 elif t<423.8:
  q=((t-400.)%19.)/19.
  if q<.60:water=q/.60;turn=0.;filling=True;draining=False
  elif q<.78:water=1-(q-.60)/.18;turn=(q-.60)/.18;filling=False;draining=True
  else:water=0.;turn=1-(q-.78)/.22;filling=False;draining=False
  bucket=turn
 elif t<430.6:
  # Water rises to the siphon threshold as described in the narration.
  initial=((423.8-400.)%19.)/19./.60
  water=initial+(1-initial)*sm(t,423.8,430.6);turn=0.;bucket=0.;filling=True;draining=False
 elif t<433.2:
  u=sm(t,430.6,433.2);water=1-u;turn=u;bucket=u;filling=False;draining=True
 elif t<439.35:
  # Refill while the counterweight returns the owl; birds restart once it is away.
  water=sm(t,433.2,439.35);turn=1-sm(t,433.2,435.2);bucket=turn;filling=True;draining=False
 elif t<454.4:
  # Hold one continuous draining beat across the 449 s cut to the bucket.
  water=1-sm(t,439.35,454.4);bucket=1-water;turn=sm(t,452.,461.6);filling=False;draining=True
 elif t<470.8:
  water=0.;bucket=1.;turn=sm(t,452.,461.6);filling=False;draining=False
 elif t<479.8:
  water=0.;bucket=1-sm(t,473.67,479.6);turn=bucket;filling=False;draining=False
 else:
  # Return to a cyclic state only once the narrator's reset is complete.
  q=((t-479.8)%19.)/19.
  if q<.60:water=q/.60;turn=0.;filling=True;draining=False
  elif q<.78:water=1-(q-.60)/.18;turn=(q-.60)/.18;filling=False;draining=True
  else:water=0.;turn=1-(q-.78)/.22;filling=False;draining=False
  bucket=turn
 return water,turn,filling,draining,bucket

def garden(t,mode,idx):
 s=F.root_scene(t,mode,idx);s.add(F.F.garden_frame());s.add(F.F.bowl_feeder());water,turn,filling,draining,bucket=garden_state(t)
 if water>.002:s.add(F.F.clear_unit(),B.matscale((-1.01,.38,.03),1.10,.83*water,1),False)
 by=.42-.22*turn;s.add(F.F.bucket(),xform((.49,by,.10),s=.78))
 if bucket>.002:s.add(F.F.clear_unit(),B.matscale((.49,by+.04,.30),.34,.28*bucket,.8),False)
 s.add(F.F.wire(),B.matscale((.49,by+.52,.52),1,.75-by,1),False)
 s.add(U.basin(),xform((-1.02,1.56,-.20),s=.60))
 for x,z in [(.35,.0),(.80,-.12)]:s.add(U.bird(False),xform((x,1.58,z),yaw=-.35+.05*math.sin(t*2),s=.78))
 s.add(U.bird(True),xform((1.35,1.57,-.12),yaw=-.85+.9*turn,s=1.20))
 s.add(B.stream(),B.matscale((-1.02,2.48,-.20),.7,.30,.7),False)
 for j in range(3):
  q=(t*1.9+j*.32)%1.;s.add(B.drop(),xform((-1.02,2.44-.28*q,-.20),s=.7),False)
 if water>.05 and filling:
  for j in range(4):
   q=(t*.65+j*.25)%1.;s.add(F.F.air_bead(),xform((-.28+.88*q,1.75,-.08),s=.7),False)
 if draining:
  for j in range(4):
   q=(t*.8+j*.25)%1.;s.add(F.F.bead(),xform((-.68+1.11*q,.25,.40),s=.65),False)
 return s

@cached
def fountain_water_marker(route):
 """Different luminous water markers distinguish the two water paths."""
 g=M();g.ell((0,0,0),(.030,.030,.030),'319abb' if route=='in' else 'b0eee4',KEY,10,6);return g

def fountain_state(t):
 # The lower chamber gradually fills from the start of the explanation;
 # the jet weakens and stops at the voiceover's 590.8–593 s line.
 transfer=F.lin(t,555.,593.);strength=1-sm(t,590.5,593.)
 return transfer,strength

def fountain(t,mode,idx):
 s=F.root_scene(t,mode,idx);s.add(F.F.fountain_frame());s.add(F.F.fountain_pipes());q,strength=fountain_state(t)
 s.add(F.F.clear_unit(),B.matscale((0,.25,.04),1.02,.06+.56*q,1),False)
 s.add(F.F.clear_unit(),B.matscale((0,1.20,.04),1.02,.59-.52*q,1),False)
 if strength>.01:
  s.add(B.stream(),B.matscale((.16,2.27,.12),.65,-.48*strength,.65),False)
  for j in range(8):
   d=(t*.78+j/4)%1.;side=-1 if j%2 else 1
   x=.16+side*.33*strength*d;y=2.27+.48*strength*(1-d*d)
   s.add(F.F.bead(),xform((x,y,.15),s=.72),False)
  routes=[([(-.15,2.12,.17),(-.80,2.12,.17),(-.80,.24,.17),(-.48,.24,.17)],fountain_water_marker('in')),
          ([(.48,1.0,.17),(.82,1.0,.17),(.82,1.88,.17),(.46,1.88,.17)],F.F.air_bead()),
          ([(.16,1.22,.17),(.16,2.27,.17)],fountain_water_marker('out'))]
  for r,(pts,mesh) in enumerate(routes):
   for j in range(4):s.add(mesh,xform(F.path_point(pts,t*(.16+.025*r)+j/4),s=.68),False)
 return s

@cached
def steam_hearth_supports():
 """Stone supports physically hold the raised cauldron above the fire."""
 g=M()
 for x in (-.58,.58):
  bevel(g,(x,.56,0),(.27,.44,.44),'b7a388',PAPER,.025)
  bevel(g,(x,.79,0),(.36,.06,.46),'8d704c',BRASS,.012)
 return g

STEAM_RAISE=.40

def steam_state(t):
 """Fire strength, steam-flow onset and a smooth angular-velocity ramp."""
 fire=sm(t,627.,629.);steam=sm(t,631.2,634.);u=max(0.,(t-634.)/6.)
 # Integral of smoothstep, so angle and rotational speed are continuous.
 turns=6.*(u**3-.5*u**4) if u<1. else 6.*(u-.5)
 angle=1.3*turns
 return fire,steam,angle

def steam(t,mode,idx):
 s=F.root_scene(t,mode,idx);s.add(F.L.stand());s.add(steam_hearth_supports())
 # Raise the entire boiler/axle assembly together, leaving an actual air gap
 # and a visible supported hearth rather than burying the flame in the vessel.
 s.add(F.L.boiler(),xform((0,STEAM_RAISE,0)));fire,steam,angle=steam_state(t)
 if fire>.015:s.add(U.flame_shape(),xform((0,.34,.05),s=(.90+.06*math.sin(t*6))*max(.20,fire)),False)
 cy=2.15+STEAM_RAISE
 if mode=='steam_cut':s.add(F.F.steam_cut(),xform((0,cy,.06),roll=angle))
 else:s.add(F.L.spinner(),xform((0,cy,0),pitch=angle))
 if steam>.015:
  for j in range(4):
   p=(t*.6+j*.25)%1.;s.add(F.F.bead(),xform((.58,1.33+STEAM_RAISE+.73*p,.04),s=.7*max(.2,steam)),False)
 if mode!='steam_cut' and t>=634.:
  ca,sa=math.cos(angle),math.sin(angle)
  for sign in (-1,1):
   for j in range(3):
    p=(t*1.4+j/3)%1.;ly=sign*.59;lz=sign*(.31+.32*p)
    s.add(F.F.steam_puff(),xform((0,cy+ca*ly-sa*lz,sa*ly+ca*lz),s=(.65+.45*p)*max(.15,sm(t,634.,636.))),False)
 return s
@cached
def stage_beacon():
 """Small stage-prop beacon and rocks, not a claim about the ancient set."""
 g=M()
 bevel(g,(0,.035,0),(.40,.07,.28),'827b6a',PAPER,.015)
 bevel(g,(0,.23,0),(.13,.39,.13),'c5af8c',PAPER,.014)
 for y in (.12,.22,.32):g.box((0,y,.071),(.12,.012,.008),'9e8c73',PAPER)
 bevel(g,(0,.44,0),(.20,.07,.19),'ae916d',PAPER,.012)
 g.lathe([(0,.035),(.02,.08),(.06,.09),(.08,.07)],(0,.48,0),'ae8754',BRASS,18)
 return g

@cached
def stage_wave():
 """A thin, moving carved stage prop; genuine geometry rather than an overlay."""
 g=M()
 pts=[(-.34,0,0),(-.25,.014,0),(-.16,.025,0),(-.07,.014,0),(.02,0,0),(.11,.012,0),(.20,.024,0),(.29,.010,0),(.34,0,0)]
 for a,b in zip(pts,pts[1:]):tube(g,a,b,.010,'b3e5dd',KEY,8,cap=False)
 return g

def theatre_story_state(t):
 # The brief introduction cuts to a prefigured sea scene. During the long
 # explanation the scenery is exchanged only while the stage doors are shut.
 intro=894.<=t<900.
 sea=intro or t>=988.
 cloud=1. if intro else sm(t,1029.27,1031.4) if sea else 0.
 wreck=sm(t,894.2,897.8) if intro else sm(t,1033.,1036.2) if sea else 0.
 return {'sea':sea,'intro':intro,'cloud':cloud,'wreck':wreck}

def theatre(t,mode,idx):
 """A paced, observable stage program plus its linked hidden motor."""
 s=F.root_scene(t,mode,idx);s.add(U.theatre_shell());a=(t-875)*.85;cam=-a*.6
 s.add(U.wheel(),xform((-.62,.61,.59),roll=a));s.add(U.wheel(),xform((.54,.62,.59),roll=cam));s.add(F.F.theatre_rig())
 s.add(F.F.theatre_weight(),xform((-1.00,.35,.31),s=.66))
 q=.45*sm(t,926,950)+.55*F.lin(t,950,1049)
 sand_height=.32*(1-q*.6);sand_top=.39+sand_height;weight_y=sand_top+.0496
 s.add(F.F.sand_unit(),B.matscale((-1.00,.39,.47),.24,sand_height,.8),False)
 s.add(F.F.weight_block(),xform((-1.00,weight_y,.37),s=.62))
 s.add(F.F.wire(),B.matscale((-1.00,weight_y+.06,.50),1,max(.04,.98-weight_y-.06),1),False)
 if 926<=t<1049:
  for j in range(4):
   d=(t*1.1+j/4)%1.;s.add(F.F.sand_grain(),xform((-1.0,.38-.17*d,.50),s=.7),False)
 opening=F.door_open(t)
 s.add(F.theatre_panel('L'),xform((-1.22,1.07,.52),yaw=-opening*2.75))
 s.add(F.theatre_panel('R'),xform((1.22,1.07,.52),yaw=opening*2.75))
 phi=((cam-math.pi/2+math.pi/8)%(math.pi/4))-math.pi/8
 lift=sm(.28-abs(phi),0,.28)
 s.add(F.bar_lever(),xform((.54,.885,.68),roll=-.085*lift,s=.25))
 state=theatre_story_state(t)
 if not state['sea']:
  # The worker, arm and visible linkage remain together for the entire
  # first scene and disappear only during a cut or a shut-door exchange.
  x=-.66+1.25*F.lin(t,887,903)
  if t>930:x=-.10+.30*math.sin((t-930)*.15)
  s.add(U.ship(),xform((x,1.18,-.05),s=.88))
  s.add(F.F.theatre_worker_rig())
  s.add(F.F.puppet_body(),xform((-.70,1.13,.05),s=.82))
  s.add(F.F.hammer_sleeve(),xform((-.70,1.13+.82*.34,.12),roll=-.32+1.05*lift,s=.82))
 else:
  # Three separate stage ships make the fleet readable. They move gently on
  # the miniature set; the lead vessel lists and sinks near the beacon rock.
  phase=(t-990.)*.12 if not state['intro'] else (t-894.)*.18
  wreck=state['wreck']
  for j,(base,z,scale) in enumerate([(-.64,.16,.48),(-.08,-.04,.43),(.47,-.20,.36)]):
   drift=.13*math.sin(phase+j*.55);bob=.015*math.sin(t*1.5+j)
   roll=.04*math.sin(t*1.2+j)
   if j==2:roll-=.78*wreck;bob-=.13*wreck
   s.add(U.ship(),xform((base+drift,1.16+bob,z),roll=roll,s=scale))
  s.add(stage_beacon(),xform((.91,1.07,-.17),s=.83))
  if state['cloud']>.02:
   s.add(U.flame_shape(),xform((.91,1.53,-.17),s=.32*state['cloud']),False)
  for j in range(3):
   s.add(stage_wave(),xform((-.78+j*.70,1.095+.007*math.sin(t*2+j),.25),s=.80),False)
  if state['intro'] or t>=1025:
   for j in range(3):s.add(F.F.dolphin(),xform((-.82+j*.50,1.16+.055*math.sin(t*2+j),.27),roll=.16*math.sin(t*2+j),s=.42))
  if state['cloud']>.02:
   s.add(F.F.thunder(),xform((.0,2.16,-.10),s=.90*state['cloud']))
 return s
