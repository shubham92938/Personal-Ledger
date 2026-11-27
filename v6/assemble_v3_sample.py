"""Assemble contiguous native v3 picture segments with their original soundtrack.

Output is an explicitly labelled sample. Timings/decodes are checked, but
picture, captions and mix still require uninterrupted human playback.
"""
from pathlib import Path
from fractions import Fraction
import argparse,hashlib,json,subprocess
import av
from imageio_ffmpeg import get_ffmpeg_exe
R=Path(__file__).resolve().parent;W=R/'work/camera-v3';D=R/'deliverables';S=R/'source';FF=get_ffmpeg_exe()

def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def assemble(labels,out,fade,audio_path=None):
 parts=[]
 for name in labels:
  path=W/(name+'.mp4');info=json.loads((W/(name+'.json')).read_text())
  if not path.exists() or digest(path)!=info['sha256']:raise RuntimeError(f'Missing/corrupt rendered segment {name}')
  parts.append((path,info))
 parts.sort(key=lambda p:p[1]['start_frame'])
 for a,b in zip(parts,parts[1:]):
  if a[1]['end_frame_exclusive']!=b[1]['start_frame']:raise ValueError('Segments are not contiguous')
  if a[1]['video_validation']['extradata']!=b[1]['video_validation']['extradata']:raise ValueError('Video encoder headers do not match')
 first=parts[0][1]['start_frame'];last=parts[-1][1]['end_frame_exclusive'];frames=last-first;duration=frames/24
 if not 0<=fade<duration:raise ValueError('Bad audio fade duration')
 lines=['ffconcat version 1.0']
 for p,r in parts:
  lines.append("file '"+str(p).replace("'","'\\''")+"'")
  lines.append('duration %.12f'%((r['end_frame_exclusive']-r['start_frame'])/24))
 fl=W/'sample-concat.ffconcat';fl.write_text('\n'.join(lines)+'\n')
 audio=Path(audio_path) if audio_path else R/'.cache/project-mix-with-user-effects.wav'
 if not audio.is_absolute():audio=R/audio
 if not audio.exists():raise FileNotFoundError('Lossless review mix is missing; regenerate it before assembling')
 out=Path(out);out=out if out.is_absolute() else D/out
 tmp=out.with_name(out.stem+'.part.mp4')
 af=f'atrim=duration={duration:.12f},asetpts=PTS-STARTPTS'
 if fade:af+=f',afade=t=out:st={duration-fade:.12f}:d={fade:.12f}'
 cmd=[FF,'-nostdin','-hide_banner','-loglevel','warning','-y','-f','concat','-safe','0','-i',str(fl),
  '-ss',f'{first/24:.12f}','-t',f'{duration:.12f}','-i',str(audio),'-map','0:v:0','-map','1:a:0',
  '-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-af',af,'-video_track_timescale','24000','-movflags','+faststart',str(tmp)]
 print('ASSEMBLING',str(out),'frames',frames,'duration',duration,flush=True);subprocess.run(cmd,check=True)
 with av.open(str(tmp)) as c:
  v=c.streams.video[0];a=c.streams.audio[0];vtime=v.time_base
  pts=sorted(Fraction(p.pts)*vtime for p in c.demux(v) if p.pts is not None)
  bad=[i for i,(p,e) in enumerate(zip(pts,(Fraction(j,24) for j in range(frames)))) if p!=e]
  report={'output':str(out.relative_to(R)),'input_segments':[x[0].name for x in parts],'film_start_s':first/24,
   'input_source_fingerprints':sorted(set(x[1].get('render_source_fingerprint','legacy-before-fingerprint') for x in parts)),
   'picture_frames_expected':frames,'picture_packets_actual':len(pts),'frame_rate':str(v.average_rate),'time_base':str(vtime),
   'bad_video_pts_count':len(bad),'first_bad_pts':bad[:10],
   'audio_start_s':float(a.start_time*a.time_base) if a.start_time is not None else None,
   'audio_duration_s':float(a.duration*a.time_base) if a.duration is not None else None,
   'soundtrack':str(audio.relative_to(R)) if audio.is_relative_to(R) else str(audio),'soundtrack_sha256':digest(audio),
   'fade_seconds':fade,'bytes':tmp.stat().st_size,'sha256':digest(tmp),
   'captions':'Existing approximate ASR alignment; not reviewed by listening.',
   'status':('Full-length review, not an approved final master. ' if first==0 and frames==27005 else 'In-progress excerpt, not the complete film. ') +
            'Human motion, narration, caption and sound review remains necessary.'}
 if len(pts)!=frames or bad or report['audio_start_s']!=0 or abs(report['audio_duration_s']-duration)>.05:
  raise RuntimeError('Assembly timing check failed: '+json.dumps(report,indent=2))
 test=subprocess.run([FF,'-nostdin','-hide_banner','-v','error','-i',str(tmp),'-map','0:v:0','-map','0:a:0','-f','null','-'],capture_output=True,text=True)
 report['decode_exit_code']=test.returncode;report['decode_errors']=test.stderr[-8000:]
 if test.returncode or test.stderr.strip():raise RuntimeError('Full sample decode failed: '+test.stderr[-3000:])
 tmp.replace(out);(S/(out.stem+' - assembly.json')).write_text(json.dumps(report,indent=2)+'\n')
 print('SAMPLE_READY',json.dumps(report,indent=2),flush=True)
 return report

def main():
 p=argparse.ArgumentParser();p.add_argument('--labels',nargs='+',required=True);p.add_argument('--out',required=True);p.add_argument('--fade',type=float,default=0.);p.add_argument('--audio')
 o=p.parse_args();assemble(o.labels,o.out,o.fade,o.audio)
if __name__=='__main__':main()
