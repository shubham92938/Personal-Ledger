"""Original 3D work-in-progress. Uses live, world-space geometry, not reference imagery.
Film time and world mechanism clocks are explicit so sound, cuts and captions can be checked.
"""
from __future__ import annotations
import os,sys,math,json,hashlib,random,time,subprocess,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'engine'))
import numpy as np
from PIL import Image,ImageFont,ImageDraw
from geo import M,I,v,norm,xform,Lens,ease,clamp
from forge import cached,bevel,tube,ring,riv,PNT,STEEL,BRASS,WOOD,PAPER,KEY,INK,CLOTH,WALL,GLASS,EMIT,CUT
from stage_cine import Stage
from imageio_ffmpeg import get_ffmpeg_exe
FF=get_ffmpeg_exe();C=ROOT/'.cache';D=ROOT/'deliverables';SRC=ROOT/'source';FPS=24;N=616
# All camera and material dimensions are reconstruction choices, not measured ancient dimensions.
STONE=('c9b99a','c2ae89','bdab8b','d1c0a0','c4b393','bda98c','cbbb9d')
SAND='c5b292';LIGHT='dfceb0';DARK='6c5842';BR='96723e';HI='d4ac61';LOW='5a4433';PAT='517066';WATR='50aeb7'

def blend(a,b,t):return v(a)+(v(b)-v(a))*ease(t)
def sm(t,a,b):return ease((t-a)/(b-a))
def matscale(pos,sx=1,sy=1,sz=1):
 m=I.copy();m[0,0]=sx;m[1,1]=sy;m[2,2]=sz;m[:3,3]=pos;return m

def uvgreen(i):return ('506743','536d47','647c4d','748858','3c5e43','4e704a')[i%6]

@cached
def paving():
 g=M();g.box((0,-.19,0),(19,.34,18),'ae9c7f',PAPER)
 r=random.Random(12227)
 for ix in range(-11,12):
  for iz in range(-11,12):
   x=ix*.78+(iz%2)*.39;z=iz*.78;c=STONE[(ix*31+iz*7)%len(STONE)]
   g.box((x,-.015+r.uniform(-.005,.004),z),(.754,.042,.754),c,PAPER)
   if (ix+iz)%8==0:g.box((x+.17,.009,z-.1),(.19,.002,.012),'9e8c70',PAPER)
 return g

@cached
def column():
 g=M();g.lathe([(0,.26),(.07,.28),(.14,.25),(.18,.2),(.22,.20),(.25,.17),(2.94,.14),(2.99,.21),(3.07,.22),(3.12,.28),(3.20,.29)],(0,0,0),'cbbca1',PAPER,28)
 for j in range(16):
  a=j*math.tau/16;x=.166*math.sin(a);z=.166*math.cos(a)
  tube(g,(x,.28,z),(x*.85,2.90,z*.85),.009,'ead9b8',PAPER,5)
 for y in (.075,.18,2.95,3.11):
  tube(g,(0,y-.025,0),(0,y+.025,0),.24 if y>.2 else .275,'d8c8ac',PAPER,28)
 bevel(g,(0,3.22,0),(.65,.10,.65),'d8c8a9',PAPER,.025)
 return g

@cached
def portico():
 g=M();
 g.box((0,1.64,-4.23),(14,3.28,.43),'a99980',WALL)
 # The portal is explicitly a staged architectural reconstruction.
 bevel(g,(0,1.25,-3.998),(2.02,2.52,.05),'554d3e',WOOD,.03)
 for x in (-1.14,1.14):bevel(g,(x,1.37,-3.9),(.24,2.78,.26),'dbccb0',PAPER,.025)
 for y in (.12,2.65,2.83):bevel(g,(0,y,-3.90),(2.57,.14,.26),'e0cdb0',PAPER,.025)
 for x in (-5.6,-3.55,3.55,5.6):
  g.box((x,1.77,-3.995),(.92,1.08,.08),'554e40',WOOD)
  for dx in (-.51,.51):g.box((x+dx,1.77,-3.92),(.11,1.25,.12),'dfccaa',PAPER)
  for y in (1.18,2.36):g.box((x,y,-3.92),(1.14,.12,.12),'dfccaa',PAPER)
  for dx in (-.24,0,.24):g.box((x+dx,1.76,-3.9),(.028,1.06,.07),'8d7252',WOOD)
 g.box((0,3.35,-3.25),(15,.28,2.1),'d6c4a4',PAPER)
 for y in (3.24,3.46):bevel(g,(0,y,-2.12),(15,.09,.30),'ded0b4',PAPER,.015)
 for j in range(-30,31):g.box((j*.24,3.3,-1.96),(.12,.12,.12),'bba98c',PAPER)
 # Recesses, sloped terracotta roofing, small scuppers.
 g.box((0,3.57,-3.16),(15,.20,2.1),'9b593e',PAPER)
 for j in range(-32,33):
  x=j*.23;tube(g,(x,3.71,-4.14),(x,3.63,-2.12),.046,'ba6d4d',PAPER,6)
 for j in range(-10,11):g.box((j*.7,.12,-3.77),(.68,.24,.42),'cbbb9e',PAPER)
 return g

@cached
def planter():
 g=M();g.lathe([(0,.16),(.05,.21),(.13,.28),(.35,.32),(.48,.24),(.5,.24),(.53,.28),(.57,.28),(.59,.22)],(0,0,0),'b87955',PAPER,24)
 tube(g,(0,.58,0),(0,.6,0),.21,'66563d',PAPER,20)
 r=random.Random(44)
 for j in range(28):
  a=j*2.39996;h=r.uniform(.55,1.04);d=r.uniform(.12,.39);x=d*math.cos(a);z=d*math.sin(a)
  tube(g,(0,.57,0),(x,h,z),.008,'5d633c',WOOD,5)
  g.ell((x,h,z),(.11,.045,.055),uvgreen(j),CLOTH,8,4)
 return g

@cached
def pedestal():
 g=M()
 bevel(g,(0,.10,0),(2.0,.20,1.65),'d5c3a5',PAPER,.025)
 bevel(g,(0,.235,0),(1.75,.10,1.4),'b9a486',PAPER,.025)
 bevel(g,(0,.32,0),(1.57,.08,1.27),'d9c8ac',PAPER,.02)
 for y in (.06,.16):g.box((0,y,.83),(1.96,.016,.016),'ab9677',PAPER)
 return g

@cached
def shell_structure():
 g=M();
 # Back and two sides are separate panels, leaving a believable hollow volume when sectioned.
 for x in (-.74,.74):bevel(g,(x,1.19,0),(.08,1.66,1.18),'7b623e',BRASS,.012)
 bevel(g,(0,1.19,-.58),(1.48,1.66,.06),'604d34',BRASS,.012)
 bevel(g,(0,.39,0),(1.55,.13,1.25),'5d4932',BRASS,.018)
 bevel(g,(0,1.99,0),(1.61,.10,1.29),'80633b',BRASS,.018)
 # A dark, hollow slot on the upper face, outlined by a raised bronze collar.
 for x in (.34,.66):bevel(g,(x,2.048,.06),(.042,.018,.20),'dbb575',BRASS,.005)
 for z in (-.03,.15):bevel(g,(.50,2.048,z),(.35,.018,.030),'dbb575',BRASS,.005)
 g.box((.50,2.052,.06),(.26,.009,.12),'111a19',PNT)
 for x in (-.78,.78):
  for z in (-.62,.62):bevel(g,(x,1.19,z),(.09,1.75,.08),HI,BRASS,.012)
  for y in (.41,1.95):bevel(g,(x,y,0),(.09,.10,1.28),HI,BRASS,.01)
 for y in (.43,1.94):bevel(g,(0,y,.62),(1.57,.09,.08),HI,BRASS,.01)
 for x in (-.78,.78):
  for y in np.linspace(.53,1.84,8):riv(g,(x,float(y),.67),(0,0,1),.022,'d5a76b',BRASS)
 return g

@cached
def front_panel():
 g=M();bevel(g,(0,1.19,.61),(1.47,1.51,.055),'967346',BRASS,.018)
 # Bronze panel with a subtly patinated central field and raised geometric bands.
 bevel(g,(0,1.23,.646),(1.12,1.12,.026),'785f3e',BRASS,.012)
 for x in (-.58,.58):bevel(g,(x,1.23,.67),(.036,1.2,.035),'caa36a',BRASS,.008)
 for y in (.64,1.82):bevel(g,(0,y,.67),(1.20,.034,.035),'caa36a',BRASS,.008)
 for x in np.linspace(-.51,.51,6):
  for y in (.70,1.76):riv(g,(float(x),y,.689),(0,0,1),.012,'ddba7c',BRASS)
 # Decorative medallion is an in-world object, not an on-screen graphic.
 tube(g,(.17,1.27,.67),(.17,1.27,.704),.22,'b58c50',BRASS,32)
 ring(g,(.17,1.27,.709),.167,.009,'e3ba71',BRASS,28,axis=2)
 tube(g,(.17,1.27,.708),(.17,1.27,.722),.032,'dfb569',BRASS,20)
 return g

@cached
def spigot():
 g=M();x=-.42
 tube(g,(x,.87,.61),(x,.87,.98),.075,'c29a61',BRASS,20)
 tube(g,(x,.87,.975),(x,.75,1.075),.064,'bd9457',BRASS,18)
 tube(g,(x,.87,.68),(x,.87,.72),.12,'88663b',BRASS,20)
 tube(g,(x,.75,1.075),(x,.73,1.075),.074,'d4ad6c',BRASS,20)
 return g

@cached
def receiving_bowl():
 g=M();x=-.42;z=1.08
 g.lathe([(.0,.12),(.04,.22),(.09,.31),(.18,.36),(.235,.37),(.25,.34),(.18,.30),(.115,.25)],(x,.31,z),'cdb186',PAPER,30)
 tube(g,(x,.424,z),(x,.430,z),.245,'4a92a0',KEY,30)
 # The bowl is supported by the masonry, not suspended beneath the tap.
 bevel(g,(x,.25,z),(.84,.13,.80),'c4b293',PAPER,.026)
 return g

@cached
def interior():
 g=M()
 # The tank is shown open to camera, with its face removed for comprehension.
 # Blue/teal is an explanatory, opaque cross section, not a claim about liquid appearance.
 bevel(g,(-.36,.52,-.26),(.61,.07,.49),'a0814d',BRASS,.012)
 for x in (-.67,-.05):bevel(g,(x,1.18,-.26),(.04,1.35,.47),'b39559',BRASS,.009)
 bevel(g,(-.36,1.18,-.47),(.63,1.35,.05),'7c6c4c',BRASS,.009)
 bevel(g,(-.36,1.75,-.30),(.58,.06,.45),'bd9f60',BRASS,.01)
 # Water visible behind the mechanism; a narrow front wall is removed.
 g.box((-.36,1.13,-.18),(.54,1.01,.032),'559da3',KEY)
 g.box((-.36,1.655,-.21),(.54,.025,.35),'80bdba',KEY)
 # Outlet chamber opening is below the moving plug. A dark gap stays legible.
 bevel(g,(-.53,.69,.22),(.32,.15,.28),'7a5d3a',BRASS,.009)
 g.box((-.53,.78,.27),(.21,.018,.15),'252d27',PNT)
 # Dark pipe represents outflow path leading to the exterior spigot.
 tube(g,(-.53,.66,.26),(-.42,.66,.60),.062,'b98f55',BRASS,14)
 # Proper axle on a vertical support; fixed backplate gives visual contrast.
 bevel(g,(.03,.73,.23),(.13,.69,.12),'8d7147',BRASS,.02)
 tube(g,(.03,1.27,.20),(.03,1.27,.49),.078,'a9824a',BRASS,18)
 return g

@cached
def lever():
 g=M();bevel(g,(0,0,0),(1.33,.07,.08),'d2aa66',BRASS,.016)
 # Shallow coin plate with a small rim. Its right edge is open so the coin can fall off.
 bevel(g,(.53,.05,0),(.42,.035,.36),'a98852',BRASS,.01)
 for z in (-.18,.18):bevel(g,(.53,.075,z),(.42,.025,.025),'e0b878',BRASS,.005)
 tube(g,(-.57,0,-.10),(-.57,0,.10),.048,'e6c27a',BRASS,14)
 tube(g,(0,0,-.1),(0,0,.1),.07,'e5bd77',BRASS,18)
 return g

@cached
def lid():
 g=M();
 # A solid plug heavier than the empty plate hangs by a rod from the left end.
 tube(g,(0,0,0),(0,.06,0),.105,'ad8448',BRASS,20)
 tube(g,(0,.06,0),(0,.57,0),.014,'d6b675',BRASS,10)
 return g

@cached
def coin():
 g=M();tube(g,(0,0,-.025),(0,0,.025),.105,'d4aa64',BRASS,28)
 ring(g,(0,0,.027),.079,.006,'f2d592',BRASS,26,axis=2)
 tube(g,(0,0,.029),(0,0,.035),.027,'a77c3d',BRASS,18)
 return g

@cached
def drop():
 g=M();g.ell((0,0,0),(.027,.046,.027),'79ccd2',KEY,10,6);return g

@cached
def stream():
 g=M();
 # Normalized vertical strand, dynamically scaled in world coordinates.
 for i in range(10):
  a=i/10;b=(i+1)/10
  tube(g,(.010*math.sin(a*10),-a,.008*math.cos(a*11)),(.010*math.sin(b*10),-b,.008*math.cos(b*11)),.024,'77c8d0',KEY,9,cap=False)
 return g

@cached
def cutpipe():
 g=M();tube(g,(-.53,.66,.27),(-.42,.66,.59),.026,'8ae0dc',KEY,10);return g

class Scene:
 def __init__(self,t,which,eye,target,fov):
  self.shot=which;self.name=which;self.time=t;self.objects=[];self.lenses={'wide':Lens(eye,target,fov,16/9)};self.lenses['short']=self.lenses['wide']
  self.sun=(-.42,.79,.44);self.warm=.25;self.sky='7098b2';self.horizon='c4c1a8';self.fog=.004;self.flow=1.;self.sea=0.;self.shadow=((0,1.0,0),12.);self.attributes={'light': {'key_power':1.64,'fill_power':.33,'light_power':.0,'expose':1.05,'aperture':3.2}}
 def add(self,m,x=I,sh=True):self.objects.append((m,x,sh))

def water_amount(t):
 if 6.88<=t<=10.3:return sm(t,6.88,7.2)*(1-sm(t,9.7,10.27))
 if 20.5<=t<=24.8:return sm(t,20.5,21.0)*(1-sm(t,24.1,24.75))
 return 0.

def make_scene(frame):
 t=frame/FPS
 if t<4.83:
  u=t/4.83;name='arrival';eye=blend((-2.6,1.82,5.5),(-1.48,1.75,4.38),u);tar=blend((-.08,1.18,0),(0,1.20,0),u);fov=39
 elif t<6.75:
  u=(t-4.83)/(6.75-4.83);name='coin-slot';eye=blend((1.25,3.10,2.85),(.95,2.90,2.19),u);tar=blend((.47,1.99,.04),(.47,1.99,.04),u);fov=31
 elif t<10.75:
  u=(t-6.75)/4;name='water';eye=blend((-1.62,1.35,2.80),(-1.25,1.23,2.43),u);tar=blend((-.42,.78,.88),(-.43,.78,1.0),u);fov=35
 elif t<14.17:
  u=(t-10.75)/(14.17-10.75);name='chest';eye=blend((2.4,1.9,4.6),(1.90,1.82,3.75),u);tar=blend((0,1.18,0),(0,1.20,0),u);fov=34
 elif t<18.83:
  u=(t-14.17)/(18.83-14.17);name='temple';eye=blend((.95,1.56,4.05),(.25,1.68,3.60),u);tar=blend((-.05,1.12,.1),(-.04,1.17,.05),u);fov=35
 else:
  u=(t-18.83)/(N/FPS-18.83);name='inside';eye=blend((.12,1.62,3.90),(.05,1.55,3.12),u);tar=blend((0,1.22,0),(0,1.21,0),u);fov=31
 s=Scene(t,name,eye,tar,fov);s.add(paving());s.add(portico())
 for x in (-6.1,-4.05,-2.,2.,4.05,6.1):s.add(column(),xform((x,0,-2.23)))
 for x,z,q in [(-2.55,-1.25,1.1),(2.6,-1.15,.88),(3.65,-2.45,.74),(-3.65,-2.5,.80)]:s.add(planter(),xform((x,0,z),s=q))
 if name=='arrival':s.add(column(),xform((-3.22,0,2.8),s=1.25))
 s.add(pedestal());s.add(shell_structure())
 section=(name=='inside')
 if not section:s.add(spigot());s.add(receiving_bowl())
 if section:
  s.add(interior())
  # The coin lands first, depresses the plate, then slides off: a single linked mechanism.
  ang=-.18*sm(t,20.35,21.1)*(1-sm(t,23.83,24.45));s.add(lever(),xform((.03,1.27,.38),roll=ang));dy=-.57*math.sin(ang);s.add(lid(),xform((-.54,.795+dy,.46)))
  x=.55 + .31*sm(t,21.65,23.75);landing=sm(t,19.18,20.05);fall=sm(t,23.76,24.4)
  # The coin follows the moving, tilted plate before it leaves the free edge.
  yy=(1-landing)*2.22+landing*(1.38+math.sin(ang)*(x-.03));yy-=fall*.70
  s.add(coin(),xform((x,yy,.38),pitch=math.pi*.5*landing,roll=ang*(1-fall)))
  if water_amount(t)>.03:s.add(cutpipe(),I,False)
 else:
  s.add(front_panel())
  if name=='coin-slot':
   a=sm(t,5.03,6.28);s.add(coin(),xform((.50,2.72-.77*a,.06)),True)
 # Water is visible only after its start cue; it narrows and stops as the mechanism resets.
 w=water_amount(t)
 if w>.015 and not section:
  s.add(stream(),matscale((-.42,.74,1.075),w**.4,.31*w**.35,w**.4),False)
  for j in range(3):
   d=(t*2.9+j*.30)%1.;s.add(drop(),xform((-.42+.012*math.sin(j*2),.71-.30*d,1.075),s=.7*w),False)
 return s

def sheets(size,frames):
 st=Stage({'wide':(size*16//9,size)});imgs=[]
 for i in frames:
  s=make_scene(i);t0=time.monotonic();st.shadow(s,i);im=st.still(s,'wide');out=C/f'proof-{i:04}-{s.name}.png';im.save(out);imgs.append((i,s.name,im));print('still',i,round(i/FPS,2),s.name,'elapsed',round(time.monotonic()-t0,2),flush=True)
 w,h=480,270;out=Image.new('RGB',(w*3,h*math.ceil(len(imgs)/3)+34*math.ceil(len(imgs)/3)), '#172027');d=ImageDraw.Draw(out);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
 for j,(i,n,m) in enumerate(imgs):
  x=j%3*w;y=j//3*(h+34);out.paste(m.resize((w,h),Image.Resampling.LANCZOS),(x,y));d.text((x+8,y+h+7),f'{i/FPS:05.2f} s · {n}',font=font,fill='#e8dfcf')
 p=C/'opening-look.jpg';out.save(p,quality=92);print('LOOK',p,flush=True)

def render(size):
 width=size*16//9;height=size;st=Stage({'wide':(width,height)});target=C/f'opening-picture-{height}.mp4';part=C/f'opening-picture-{height}.part.mp4'
 # ASS is based on original words, manually checked against the generated recording.
 ass=SRC/'opening-captions.ass'
 p=subprocess.Popen([FF,'-nostdin','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgba','-s',f'{width}x{height}','-r',str(FPS),'-i','-','-filter_threads','1','-vf',f"vflip,ass='{ass.as_posix()}',scale=in_range=full:out_range=tv:out_color_matrix=bt709,format=yuv420p",'-threads','2','-c:v','libx264','-preset','veryfast','-crf','19','-g','48','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-video_track_timescale','24000','-an',str(part)],stdin=subprocess.PIPE)
 start=time.monotonic()
 try:
  for i in range(N):
   s=make_scene(i);st.shadow(s,i);p.stdin.write(st.frame(s,'wide'))
   if i%96==0:print('FRAME',i,'/',N,'shot',s.name,'fps',round((i+1)/(time.monotonic()-start),2),flush=True)
 finally:p.stdin.close();rc=p.wait()
 if rc:raise RuntimeError('ffmpeg failed '+str(rc))
 part.replace(target);print('PICTURE_READY',target,target.stat().st_size,'seconds',round(time.monotonic()-start,2),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--sheet',action='store_true');p.add_argument('--size',type=int,default=540);p.add_argument('--frames',nargs='*',type=int,default=[0,72,130,160,188,224,268,338,420,456,480,516,558,594,615]);a=p.parse_args()
 if a.sheet:sheets(a.size,a.frames)
 else:render(a.size)
