"""New original world-space look-development for the long-form opening montage.
Visuals are speculative reconstructions of the written descriptions, not claims of exact archaeology.
"""
from __future__ import annotations
import os,math,sys,subprocess,time,argparse
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import build_opening as B
from geo import M,I,v,xform,ease,clamp
from forge import cached,bevel,tube,ring,riv,BRASS,WOOD,PAPER,KEY,PNT,CLOTH,EMIT
from stage_cine import Stage
R=Path(__file__).resolve().parent;C=R/'.cache';S=R/'source';FF=B.FF;FPS=24;N=376

def mix(a,b,u):return v(a)+(v(b)-v(a))*ease(u)
def smooth(t,a,b):return ease((t-a)/(b-a))

@cached
def temple_shell():
 g=M();bevel(g,(0,.28,0),(3.55,.39,2.72),'d8c6a6',PAPER,.036)
 bevel(g,(0,.49,0),(3.26,.12,2.48),'b9a286',PAPER,.022)
 g.box((0,1.58,-1.0),(2.85,2.20,.32),'605747',PAPER)
 for x in (-1.32,1.32):bevel(g,(x,1.53,.66),(.51,2.10,.34),'d7c8ac',PAPER,.028)
 for y,h in [(2.60,.22),(2.77,.13),(2.87,.10)]:bevel(g,(0,y,.62),(3.15,h,.40),'ddceaf',PAPER,.025)
 for y in (.62,1.18,1.74,2.3):
  for x in (-1.32,1.32):g.box((x,y,.85),(.50,.016,.012),'af9e80',PAPER)
 # A shallow front pediment, extruded as real geometry rather than an overlay.
 g.tri((-1.48,2.93,.86),(1.48,2.93,.86),(0,3.60,.86),'d8c6a5',PAPER)
 g.tri((-1.48,2.93,.46),(0,3.60,.46),(1.48,2.93,.46),'c0ae8e',PAPER)
 g.quad((-1.48,2.93,.46),(-1.48,2.93,.86),(0,3.60,.86),(0,3.60,.46),'bfa887',PAPER)
 g.quad((0,3.60,.46),(0,3.60,.86),(1.48,2.93,.86),(1.48,2.93,.46),'bfa887',PAPER)
 tube(g,(-1.52,2.94,.89),(0,3.62,.89),.035,'efe2c7',PAPER,8);tube(g,(0,3.62,.89),(1.52,2.94,.89),.035,'efe2c7',PAPER,8)
 return g

@cached
def leaf(left):
 g=M();d=1 if left else -1;xc=d*.48
 bevel(g,(xc,1.02,0),(.94,2.02,.10),'795538',WOOD,.018)
 for j in range(5):
  x=d*(.09+j*.19);g.box((x,1.02,.059),(.016,1.91,.01),'b58a52',BRASS)
 for y in (.14,.99,1.9):bevel(g,(xc,y,.07),(.91,.08,.045),'ac854e',BRASS,.01)
 for y in (.27,1.73):
  for x in (.11,.48,.84):riv(g,(d*x,y,.10),(0,0,1),.018,'e1bd79',BRASS)
 return g

@cached
def altar():
 g=M();bevel(g,(0,.13,0),(.85,.26,.82),'c9b593',PAPER,.025);bevel(g,(0,.50,0),(.62,.49,.6),'b9a486',PAPER,.03)
 bevel(g,(0,.79,0),(.83,.12,.81),'d5c5a5',PAPER,.025)
 g.lathe([(0,.20),(.05,.27),(.12,.28),(.16,.22)],(0,.85,0),'68482e',BRASS,28)
 return g

@cached
def flame_shape():
 g=M();g.ell((0,.16,0),(.13,.22,.13),'ff8631',EMIT,12,7);g.ell((.03,.36,0),(.075,.19,.075),'ffb647',EMIT,12,7);g.ell((-.025,.12,.08),(.055,.09,.045),'ffdf8d',EMIT,10,6);return g

@cached
def basin():
 g=M();g.lathe([(0,.16),(.08,.21),(.53,.28),(.58,.37),(.65,.45),(.72,.67),(.79,.72),(.85,.68),(.74,.59)],(0,0,0),'d6c4a1',PAPER,32)
 tube(g,(0,.74,0),(0,.755,0),.58,'4a93a5',KEY,32)
 for a in (0,2.1,4.2):tube(g,(0,.77,0),(.52*math.cos(a),.77,.52*math.sin(a)),.007,'94c8c0',KEY,8)
 return g

@cached
def bird(owl=False):
 g=M();color='9e7344' if owl else 'b38b52';head='d1aa68'
 g.ell((0,.18,0),(.13,.20,.10) if owl else (.15,.13,.09),color,BRASS,16,10)
 g.ell((0,.39 if owl else .31,0),(.13,.12,.09),head,BRASS,16,9)
 # Sculptural feather relief, not a photographic or living animal.
 for dx in (-.06,.06):
  g.ell((dx,.41 if owl else .34,.088),(.04,.045,.018),'d9be82',BRASS,10,6)
  g.ell((dx,.41 if owl else .34,.106),(.015,.019,.008),'302c25',PNT,8,5)
 g.tri((-.025,.37,.112),(.025,.37,.112),(0,.33,.18),'ce9252',BRASS)
 for x in (-1,1):
  g.ell((x*.12,.18,-.008),(.055,.15,.067),'826644',BRASS,12,7)
 for dx in (-.045,.045):tube(g,(dx,.01,0),(dx,.085,0),.012,'ad864a',BRASS,8)
 tube(g,(-.15,.01,0),(.15,.01,0),.025,'765e3b',WOOD,12)
 return g

@cached
def birdstand():
 g=M();bevel(g,(0,.14,0),(2.9,.28,1.62),'b6a282',PAPER,.022)
 bevel(g,(0,.35,0),(2.64,.14,1.42),'dfcfb0',PAPER,.025)
 return g

@cached
def theatre_shell():
 g=M();
 bevel(g,(0,.16,0),(3.1,.31,1.5),'bca789',PAPER,.025)
 # Exposed lower machinery bay contrasts with the painted miniature stage above.
 for x in (-1.28,1.28):bevel(g,(x,.64,0),(.19,.68,1.12),'826343',WOOD,.02)
 bevel(g,(0,.97,0),(2.78,.18,1.34),'a57d4e',WOOD,.018)
 g.box((0,.62,-.54),(2.5,.65,.08),'4b4031',WOOD)
 g.box((0,1.68,-.44),(2.5,1.36,.12),'8db7b7',PAPER)
 g.box((0,1.04,.0),(2.5,.06,1.0),'286e83',KEY)
 for x in (-1.31,1.31):bevel(g,(x,1.68,.40),(.22,1.46,.24),'d1b187',PAPER,.02)
 for y in (1.04,2.36):bevel(g,(0,y,.42),(2.75,.12,.25),'d1b187',PAPER,.02)
 g.tri((-1.36,2.45,.5),(1.36,2.45,.5),(0,3.02,.5),'bf8864',PAPER)
 for j in range(-8,9):bevel(g,(j*.155,2.40,.55),(.075,.10,.04),'ddc6a2',PAPER,.008)
 for x in (-1.05,1.05):
  for y in (1.16,1.5,1.84,2.18):riv(g,(x,y,.54),(0,0,1),.019,'e1bd79',BRASS)
 return g

@cached
def wheel():
 g=M();ring(g,(0,0,0),.23,.025,'c5a06a',BRASS,24,axis=2)
 for j in range(8):
  a=j*math.tau/8;tube(g,(0,0,0),(.22*math.cos(a),.22*math.sin(a),0),.014,'d4b574',BRASS,8)
  g.ell((.22*math.cos(a),.22*math.sin(a),.024),(.036,.036,.025),'d7ac65',BRASS,8,5)
 tube(g,(0,0,-.03),(0,0,.03),.05,'e4bd79',BRASS,16)
 return g

@cached
def ship():
 g=M();
 # Small model hull with a mast and sail; explicitly a mechanical stage prop.
 g.box((0,0,0),(.68,.13,.19),'735239',WOOD)
 g.tri((-.44,.04,.10),(-.34,-.075,.10),(-.34,.05,.10),'8b6240',WOOD)
 g.tri((.44,.04,.10),(.34,.05,.10),(.34,-.075,.10),'8b6240',WOOD)
 tube(g,(0,.06,0),(0,.51,0),.017,'b7905c',WOOD,8)
 g.quad((-.26,.12,.01),(-.26,.48,.01),(.25,.48,.01),(.25,.12,.01),'eee0c2',CLOTH)
 tube(g,(-.29,.48,0),(.29,.48,0),.013,'95724a',WOOD,8)
 return g

def scene(i):
 t=i/FPS
 if t<5.35:
  u=t/5.35;name='fire-doors';eye=mix((4.25,2.9,8.3),(3.12,2.55,6.60),u);target=mix((0,1.55,.48),(0,1.62,.58),u);s=B.Scene(t,name,eye,target,35)
  s.add(B.paving());s.add(B.portico(),xform((0,0,-3.65)))
  s.add(temple_shell())
  for x in (-1.40,1.40):s.add(B.column(),xform((x,.50,.96),s=.67))
  opening=smooth(t,2.4,4.7)*.98
  s.add(leaf(True),xform((-.96,.52,.78),yaw=-opening));s.add(leaf(False),xform((.96,.52,.78),yaw=opening))
  s.add(altar(),xform((0,0,2.75)));f=.86+.14*math.sin(t*5.);s.add(flame_shape(),xform((0,.98,2.75),s=f),False)
  s.add(B.planter(),xform((-2.7,0,.1),s=.85));s.add(B.planter(),xform((2.7,0,.1),s=.85))
 elif t<8.45:
  u=(t-5.35)/(8.45-5.35);name='singing-garden';eye=mix((2.8,2.0,5.3),(2.0,1.80,4.23),u);target=mix((0,.95,0),(.08,1.10,0),u);s=B.Scene(t,name,eye,target,32)
  s.add(B.paving());s.add(B.portico(),xform((0,0,-1.6)));s.add(birdstand());s.add(basin(),xform((-.5,.41,.0)))
  for x,z in [( .55,.08),(.98,-.05)]:s.add(bird(False),xform((x,.50,z),yaw=-.3,s=.78))
  s.add(bird(True),xform((.74,.50,-.38),yaw=-.9+.9*smooth(t,6.1,8.0),s=1.3))
  for i0 in range(3):
   d=(t*1.9+i0*.31)%1.;s.add(B.drop(),xform((-.5,1.42-.63*d,.0),s=.9),False)
  s.add(B.stream(),B.matscale((-.5,1.41,0),.75,.63,.75),False)
  s.add(B.planter(),xform((-2.3,0,-.3),s=.75));s.add(B.planter(),xform((2.3,0,-.3),s=.75))
 else:
  u=(t-8.45)/(N/FPS-8.45);name='automatic-theatre';eye=mix((3.10,2.2,6.8),(1.3,2.08,4.75),u);target=mix((0,1.35,0),(0,1.46,0),u);s=B.Scene(t,name,eye,target,33)
  s.add(B.paving());s.add(B.portico(),xform((0,0,-3.6)));s.add(theatre_shell())
  s.add(wheel(),xform((-.62,.61,.59),roll=2.3*(t-8.45)));s.add(wheel(),xform((.54,.62,.59),roll=-1.3*(t-8.45)))
  q=clamp((t-8.45)/7.);s.add(ship(),xform((-.65+1.24*q,1.17,-.02),s=1.05))
  s.add(B.planter(),xform((-2.42,0,-.36),s=.75));s.add(B.planter(),xform((2.42,0,-.36),s=.75))
 return s

def sheet(size):
 st=Stage({'wide':(size*16//9,size)});ims=[]
 for i in (0,60,116,129,155,201,235,295,355,375):
  s=scene(i);st.shadow(s,i);im=st.still(s,'wide');ims.append((i,s.name,im));im.save(C/f'montage-{i:04}.png');print('still',i,s.name,flush=True)
 w,h=480,270;out=Image.new('RGB',(1440,math.ceil(len(ims)/3)*(h+30)),'#172027');d=ImageDraw.Draw(out);F=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
 for j,(i,n,im) in enumerate(ims):
  x=j%3*w;y=j//3*(h+30);out.paste(im.resize((w,h),Image.Resampling.LANCZOS),(x,y));d.text((x+7,y+h+6),f'{i/FPS:.2f}s · {n}',font=F,fill='#e9dece')
 out.save(C/'montage-look.jpg',quality=91)

def render(size):
 w=size*16//9;h=size;st=Stage({'wide':(w,h)});out=C/f'montage-picture-{h}.mp4';part=C/f'montage-picture-{h}.part.mp4';ass=S/'montage-captions.ass'
 p=subprocess.Popen([FF,'-nostdin','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgba','-s',f'{w}x{h}','-r',str(FPS),'-i','-','-filter_threads','1','-vf',f"vflip,ass='{ass.as_posix()}',scale=in_range=full:out_range=tv:out_color_matrix=bt709,format=yuv420p",'-threads','2','-c:v','libx264','-preset','veryfast','-crf','19','-g','48','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-video_track_timescale','24000','-an',str(part)],stdin=subprocess.PIPE)
 stime=time.monotonic()
 try:
  for i in range(N):
   s=scene(i);st.shadow(s,i);p.stdin.write(st.frame(s,'wide'))
   if i%96==0:print('FRAME',i,'/',N,s.name,'fps',round((i+1)/(time.monotonic()-stime),2),flush=True)
 finally:p.stdin.close();rc=p.wait()
 if rc:raise RuntimeError('FFmpeg failed '+str(rc))
 part.replace(out);print('MONTAGE_READY',out,out.stat().st_size,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--sheet',action='store_true');p.add_argument('--size',type=int,default=540);a=p.parse_args();sheet(a.size) if a.sheet else render(a.size)
