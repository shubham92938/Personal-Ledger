"""Create a contact sheet and simple exposure/sharpness report from rendered PNGs."""
import argparse, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("images", nargs="+", type=Path)
p.add_argument("--out", type=Path, default=Path("review-v6"))
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=True)
rows=[]; thumbs=[]
for path in a.images:
    im=Image.open(path).convert("RGB")
    arr=np.asarray(im,dtype=np.float32)/255.0
    lum=arr[:,:,0]*.2126+arr[:,:,1]*.7152+arr[:,:,2]*.0722
    # A simple high-frequency proxy, not a perceptual quality score.
    sharp=float(np.abs(np.diff(lum,axis=0)).mean()+np.abs(np.diff(lum,axis=1)).mean())
    row={"file":str(path),"width":im.width,"height":im.height,
         "mean_luma":round(float(lum.mean()),4),
         "shadow_fraction_below_0_02":round(float((lum<.02).mean()),4),
         "highlight_fraction_above_0_98":round(float((lum>.98).mean()),4),
         "edge_energy_proxy":round(sharp,5)}
    rows.append(row)
    im.thumbnail((480,270))
    thumbs.append((im.copy(),path.name,row))
(a.out/"metrics.json").write_text(json.dumps(rows,indent=2),encoding="utf-8")
cell_w,cell_h=500,315
sheet=Image.new("RGB",(cell_w*2,cell_h*((len(thumbs)+1)//2)),"#17191c")
d=ImageDraw.Draw(sheet)
for i,(im,name,r) in enumerate(thumbs):
    x=(i%2)*cell_w+10;y=(i//2)*cell_h+8
    sheet.paste(im,(x,y))
    d.text((x,y+274),f"{name} | mean {r['mean_luma']:.3f} | clip {r['highlight_fraction_above_0_98']:.3f}",fill="white")
sheet.save(a.out/"contact-sheet.jpg",quality=92)
print(a.out/"contact-sheet.jpg")
print(a.out/"metrics.json")
print("Note: metrics are screening signals, not automatic visual approval.")
