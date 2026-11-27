"""Continuing look-development assets for later long-form chapters.
The models are explanatory reconstructions, not archaeological artifacts.
"""
from pathlib import Path
import math
from PIL import Image,ImageDraw,ImageFont
import build_opening as B
import build_montage as U
from geo import M,xform
from forge import cached,bevel,tube,BRASS,PAPER,KEY,PNT,WOOD
from stage_cine import Stage
R=Path(__file__).resolve().parent;C=R/'.cache';D=R/'deliverables'

@cached
def stand():
 g=M();bevel(g,(0,.13,0),(2.82,.26,2.1),'c9b493',PAPER,.03);bevel(g,(0,.29,0),(2.52,.10,1.84),'e1d1b5',PAPER,.025);return g

@cached
def fountain_vessels():
 g=M();
 # Fronts are sectioned away to reveal the fluid. Bronze frames show two sealed chambers.
 for y in (.78,1.65):
  for x in (-.52,.52):bevel(g,(x,y,0),(.09,.78,.74),'b89960',BRASS,.012)
  for yy in (y-.38,y+.38):bevel(g,(0,yy,0),(1.10,.075,.75),'c8a66c',BRASS,.012)
  g.box((0,y,-.33),(1,.70,.045),'625641',BRASS)
  for x in (-.52,.52):
   for yy in (y-.24,y+.24):tube(g,(x,yy,.39),(x,yy,.42),.028,'e3c289',BRASS,10)
 # Water surfaces reflect the currently shown state, with open faces for the diagram.
 g.box((0,.62,.05),(.95,.37,.05),'438d9c',KEY);g.box((0,.81,.0),(.95,.025,.56),'80c7c6',KEY)
 g.box((0,1.59,.05),(.95,.46,.05),'438d9c',KEY);g.box((0,1.83,.0),(.95,.025,.56),'80c7c6',KEY)
 # Upper basin and nozzle.
 g.lathe([(0,.21),(.06,.32),(.10,.49),(.16,.63),(.20,.66),(.23,.61),(.16,.53)],(0,2.29,0),'d1b98d',PAPER,32)
 tube(g,(0,2.45,0),(0,2.47,0),.49,'5aa7b2',KEY,28)
 return g

@cached
def fountain_tubes():
 g=M();
 # Color-topped bronze paths: water from bowl to lower chamber; trapped air lower→middle;
 # pressurized water middle→jet. Paths run outside the sectioned chambers.
 paths=[([(-.18,2.33,.05),(-.85,2.33,.05),(-.85,.60,.05),(-.52,.60,.05)],'58b4bb'),
        ([(.40,1.05,.08),(.80,1.05,.08),(.80,1.93,.08),(.52,1.93,.08)],'d7a35f'),
        ([(.18,1.34,.09),(.18,2.70,.09)],'58b4bb')]
 for points,col in paths:
  for a,b in zip(points,points[1:]):
   tube(g,a,b,.045,'9a7747',BRASS,12);tube(g,(a[0],a[1],a[2]+.047),(b[0],b[1],b[2]+.047),.012,col,KEY,8)
 return g

@cached
def boiler():
 g=M()
 # Metal boiler and balanced stand.
 g.lathe([(0,.31),(.09,.43),(.50,.49),(.80,.45),(.86,.34),(.90,.30)],(0,.42,0),'a77c48',BRASS,32)
 for y in (.47,1.23):tube(g,(0,y,0),(0,y+.035,0),.45,'d2a56b',BRASS,30)
 for x in (-.58,.58):
  tube(g,(x,.41,0),(x,2.15,0),.045,'ac8b5a',BRASS,14)
  bevel(g,(x,.42,0),(.34,.12,.34),'bba583',PAPER,.02)
 # One support conveys steam from the boiler to the hollow sphere's axle.
 tube(g,(.23,1.30,0),(.58,1.30,0),.047,'c2a06a',BRASS,16)
 return g

@cached
def spinner():
 g=M();g.ell((0,0,0),(.45,.45,.45),'bb9257',BRASS,32,16)
 # Bent tubes project from opposite sides and discharge tangentially in opposite directions.
 for sign in (-1,1):
  tube(g,(0,sign*.40,0),(0,sign*.59,0),.045,'d5b17a',BRASS,14)
  tube(g,(0,sign*.59,0),(0,sign*.59,sign*.28),.045,'d5b17a',BRASS,14)
  tube(g,(0,sign*.59,sign*.28),(0,sign*.59,sign*.30),.055,'e4c18b',BRASS,14)
 return g

def scene(which,t):
 if which=='fountain':
  s=B.Scene(t,which,(3.1,2.8,6.2),(0,1.65,0),34);s.add(B.paving());s.add(B.portico(),xform((0,0,-3.1)));s.add(stand());s.add(fountain_vessels());s.add(fountain_tubes())
  for j in range(5):
   q=(t*1.5+j*.19)%1.;s.add(B.drop(),xform((.18,2.7+.44*math.sin(q*math.pi),.09),s=.7),False)
  s.add(B.planter(),xform((-2.3,0,-.4),s=.75));s.add(B.planter(),xform((2.3,0,-.4),s=.75))
 else:
  s=B.Scene(t,which,(3.5,2.2,6.8),(0,1.42,0),33);s.add(B.paving());s.add(B.portico(),xform((0,0,-3.1)));s.add(stand());s.add(boiler());s.add(spinner(),xform((0,2.15,0),pitch=t*2))
  s.add(U.flame_shape(),xform((0,.39,.12),s=.8),False)
  s.add(B.planter(),xform((-2.3,0,-.4),s=.75));s.add(B.planter(),xform((2.3,0,-.4),s=.75))
 return s

def make():
 st=Stage({'wide':(960,540)});a=[]
 for name,t in [('fountain',0),('fountain',.8),('steam',0),('steam',.8)]:
  q=scene(name,t);st.shadow(q,int(t*24));im=st.still(q,'wide');p=C/f'lab-{name}-{t:.1f}.png';im.save(p);a.append((name,t,im));print('still',p,flush=True)
 w,h=600,338;out=Image.new('RGB',(1200,2*(h+32)),'#172027');d=ImageDraw.Draw(out);f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
 for j,(name,t,im) in enumerate(a):
  x=j%2*w;y=j//2*(h+32);out.paste(im.resize((w,h),Image.Resampling.LANCZOS),(x,y));d.text((x+8,y+h+5),f'{name} · prototype at {t:.1f} s',font=f,fill='#d9e5e6')
 out.save(C/'lab-study.jpg',quality=92)
if __name__=='__main__':make()
