"""Snapshot the source and inputs which determine a v3 picture segment."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent
FILES=('render_v3.py','v3_manifest.py','build_film_v3.py','film_sequences_v3.py',
 'film_rigs_v3.py','stage_cine_v3.py','build_film.py','film_models.py',
 'build_opening.py','build_montage.py','build_lab.py','engine/geo.py',
 'engine/forge.py','engine/stage_fast.py','engine/stage_cine.py',
 'source/limestone-material.png','source/opening-captions.ass','source/longform-alignment.json')

def filehash(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def capture():
 out={}
 for name in FILES:
  p=R/name
  if not p.is_file():raise FileNotFoundError('Required picture source missing: '+name)
  out[name]=filehash(p)
 return out

def fingerprint(files):
 return hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
