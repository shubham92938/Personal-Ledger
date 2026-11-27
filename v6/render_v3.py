"""Native 1080p, 24-unique-frame camera/rig revision. NOT a final master.

Each render range has exact frame boundaries and its own approximate spoken
captions. Picture is generated from scene geometry, not resized old footage.
This does not upload or publish anything.
"""
from pathlib import Path
from fractions import Fraction
import argparse,hashlib,json,subprocess,time,textwrap
import av
import build_film_v3 as V
import v3_manifest as manifest
from stage_cine_v3 import Stage
from imageio_ffmpeg import get_ffmpeg_exe
R=Path(__file__).resolve().parent
W=R/'work'/'camera-v3';W.mkdir(parents=True,exist_ok=True)
S=R/'source';FF=get_ffmpeg_exe();FPS=24

def ass_for(a,b,path):
 data=json.loads((S/'longform-alignment.json').read_text())['cues']
 hdr=(S/'opening-captions.ass').read_text().split('[Events]')[0]+'[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'
 def clock(t):
  cs=max(0,round(t*100));h,cs=divmod(cs,360000);m,cs=divmod(cs,6000);s,cs=divmod(cs,100)
  return f'{h}:{m:02d}:{s:02d}.{cs:02d}'
 for x in data:
  if x['end']<=a or x['start']>=b:continue
  text='\\N'.join(textwrap.wrap(x['text'],width=43,break_long_words=False,break_on_hyphens=False))
  hdr+=f"Dialogue: 0,{clock(max(a,x['start'])-a)},{clock(min(b,x['end'])-a)},Narration,,0,0,0,,{text}\n"
 path.write_text(hdr)

def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for x in iter(lambda:f.read(1024*1024),b''):h.update(x)
 return h.hexdigest()

def video_check(path,count):
 with av.open(str(path)) as c:
  s=c.streams.video[0];pts=sorted(Fraction(p.pts)*s.time_base for p in c.demux(s) if p.pts is not None)
  bad=[i for i,(a,b) in enumerate(zip(pts,(Fraction(j,FPS) for j in range(count)))) if a!=b]
  out={'packets':len(pts),'expected_frames':count,'bad_pts_count':len(bad),'first_bad_pts':bad[:5],
   'resolution':[s.width,s.height],'frame_rate':str(s.average_rate),'codec':s.codec_context.name,'time_base':str(s.time_base),
   'extradata':(s.codec_context.extradata or b'').hex()}
  if len(pts)!=count or bad or s.width!=1920 or s.height!=1080 or Fraction(s.average_rate)!=FPS:raise RuntimeError('Bad video: '+json.dumps(out))
 return out

def render(start,end,label):
 if start<0 or end<=start:raise ValueError('Invalid exact frame range')
 source_files=manifest.capture();source_fingerprint=manifest.fingerprint(source_files)
 start_t=start/FPS;end_t=end/FPS;count=end-start
 ass=W/f'{label}.ass';ass_for(start_t,end_t,ass)
 out=W/f'{label}.mp4';part=W/f'{label}.part.mp4'
 filt=f"vflip,ass='{ass.as_posix()}',scale=in_range=full:out_range=tv:out_color_matrix=bt709,format=yuv420p"
 cmd=[FF,'-nostdin','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgba','-s','1920x1080','-r',str(FPS),'-i','-','-filter_threads','1','-vf',filt,'-threads','2','-c:v','libx264','-preset','veryfast','-crf','20','-maxrate','3500k','-bufsize','7000k','-g','48','-keyint_min','48','-sc_threshold','0','-profile:v','high','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-video_track_timescale','24000','-movflags','+faststart','-an',str(part)]
 st=Stage({'wide':(1920,1080)});begin=time.monotonic()
 # Warm up the motion-vector history without encoding the previous frame.
 if start>0:
  prev=V.scene((start-1)/FPS);st.shadow(prev,start-1);st.frame(prev,'wide')
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 try:
  for frame in range(start,end):
   t=frame/FPS;q=V.scene(t);st.shadow(q,frame);p.stdin.write(st.frame(q,'wide'))
   done=frame-start+1
   if done==1 or done%48==0 or done==count:
    print('RENDER',label,'FRAME',done,'/',count,'FILM',round(t,2),'SHOT',q.name,'fps',round(done/(time.monotonic()-begin),2),flush=True)
 except BaseException:
  try:p.stdin.close()
  except BrokenPipeError:pass
  p.wait();raise
 p.stdin.close();code=p.wait()
 if code:raise RuntimeError('ffmpeg encoder exited '+str(code))
 if manifest.capture()!=source_files:raise RuntimeError('Picture sources changed mid-segment; do not commit mixed-provenance render')
 validation=video_check(part,count);part.replace(out)
 record={'segment':label,'start_frame':start,'end_frame_exclusive':end,'start_s':start_t,'end_s':end_t,
  'render_source_fingerprint':source_fingerprint,'render_source_files':source_files,
  'source_and_output_fps':24,'geometry_frames_evaluated':count,'native_resolution':'1920x1080',
  'camera_blur':'depth-aware reprojection of previous camera; no blended old frames',
  'captions':'burned in from approximate ASR-aligned authored cues; human timing review needed',
  'render_seconds':round(time.monotonic()-begin,2),'bytes':out.stat().st_size,'sha256':sha(out),'video_validation':validation,
  'status':'In-progress sample / review picture, not a finished film.'}
 (W/f'{label}.json').write_text(json.dumps(record,indent=2)+'\n')
 print('SEGMENT_READY',json.dumps(record),flush=True)
 return out

def main():
 a=argparse.ArgumentParser();a.add_argument('--start-frame',type=int,required=True);a.add_argument('--end-frame',type=int,required=True);a.add_argument('--label',required=True)
 opt=a.parse_args();render(opt.start_frame,opt.end_frame,opt.label)
if __name__=='__main__':main()
