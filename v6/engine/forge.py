"""Small precision-machined forgings and typography helpers."""
import math,random,string
from functools import lru_cache
import numpy as np
from geo import M,v,norm,xform,I,TAU,clamp,ease
PNT,STEEL,BRASS,WOOD,RUBBER,PAPER,KEY,INK,CLOTH,WALL,GLASS,EMIT,LEATHER,CUT,CHROME,DUST=range(16)
def cached(fn):
    @lru_cache(maxsize=None)
    def deco(*a,**kw):
        o=fn(*a,**kw)
        if isinstance(o,M):o.rows=np.asarray(o.rows,dtype='f4')
        return o
    return deco

def bevel(g,p,d,c,k=STEEL,r=.044):
    if r<=0:g.box(p,d,c,k);return
    h=v(d)*.5;r=min(r,float(h.min())*.92);p=v(p);h2=h-r
    pt=lambda a,s: p+v([s[i]*(h[i] if i==a else h2[i]) for i in range(3)])
    axis=lambda a,s:v([s if i==a else 0 for i in range(3)])
    for a in range(3):
        b=(a+1)%3;d0=(a+2)%3
        for n in (-1.,1.):
            q=[]
            for u,w in ((-1,-1),(1,-1),(1,1),(-1,1)):
                s=[0.,0.,0.];s[a]=n;s[b]=u;s[d0]=w;q.append(pt(a,s))
            g.quad(*q,c,k,(axis(a,n),)*4)
        for sb in (-1.,1.):
            for sd in (-1.,1.):
                s=[0.,0.,0.];s[b]=sb;s[d0]=sd;s[a]=-1.;t=s.copy();t[a]=1.
                g.quad(pt(b,s),pt(b,t),pt(d0,t),pt(d0,s),c,k,(axis(b,sb),axis(b,sb),axis(d0,sd),axis(d0,sd)))
    for sx in (-1,1):
        for sy in (-1,1):
            for sz in (-1,1):
                a=(sx,sy,sz);g.tri(pt(0,a),pt(1,a),pt(2,a),c,k,(axis(0,sx),axis(1,sy),axis(2,sz)))

def tube(g,a,b,r,c,k=STEEL,n=16,r2=None,cap=True):g.sleeve(a,b,r,r if r2 is None else r2,c,k,n,cap)
def ring(g,p,r,w,c,k=STEEL,n=32,axis=2):
    p=v(p);a=(axis+1)%3;b=(axis+2)%3;pts=[]
    for j in range(n+1):
        q=p.copy();t=j*TAU/n;q[a]+=math.cos(t)*r;q[b]+=math.sin(t)*r;pts.append(q)
    for e0,e1 in zip(pts,pts[1:]):tube(g,e0,e1,w,c,k,7,cap=False)
def bar(g,a,b,w,d,c,k=STEEL,r=.023):
    a,b=v(a),v(b);delta=b-a;u=norm(delta);q=norm(np.cross((1.,0.,0.),u));q=q if np.linalg.norm(q)>.2 else v((0,1,0));p=norm(np.cross(u,q));t=I.copy();t[:3,:3]=np.stack([p,q,u],1);t[:3,3]=(a+b)*.5;m=M();bevel(m,(0,0,0),(w,d,np.linalg.norm(delta)),c,k,r);g.add(m,t)

def riv(g,o,n,r=.024,c='8d9087',k=STEEL):
    a=v(o);n=norm(n);tube(g,a-n*.015,a+n*r*.60,r,c,k,8,r*.71)


def rot(axis,angle):
    x,y,z=axis;c=math.cos(angle);s=math.sin(angle);t=1-c
    return v(((c+x*x*t,x*y*t-z*s,x*z*t+y*s),(y*x*t+z*s,c+y*y*t,y*z*t-x*s),(z*x*t-y*s,z*y*t+x*s,c+z*z*t)))

def transform(p,b=None):
    q=I.copy();q[:3,3]=p
    if b is not None:q[:3,:3]=b
    return q

def rect_ring(x,z,rx,rz,r,n=6):
    for j,(a,b) in enumerate(((1,1),(-1,1),(-1,-1),(1,-1))):
        for k in range(n+1):
            t=(j+k/n)*math.pi/2;cx,cz=math.cos(t),math.sin(t);yield (x+a*(rx-r)+r*cx,z+b*(rz-r)+r*cz,cx,cz)

def deck(g,p,w,d,r,h,c,k,cap=True,n=7):
    # Rounded rectangle with three polished chamfer bands at each edge.
    x,y,z=p;b=h*.5;b0=min(b*.61,r*.48);data=[]
    for i in range(3):
        a=i*math.pi/4;data.append((-b+b0*(1-math.cos(a)), b0*(1-math.sin(a)),math.sin(a),-math.cos(a)))
    data.extend([(b-b0,b0*(1-math.sin(a)),math.sin(a),math.cos(a)) if a==math.pi/2 else (b-b0+b0*math.cos(a),b0*(1-math.sin(a)),math.sin(a),math.cos(a)) for a in (math.pi/2,math.pi/4,0.)]);rows=[]
    for yy,t,cx,cy in data:
        rr=max(.003,r-t)
        rows.append([((a,y+yy,b),(cx*i,cy,cx*j)) for a,b,i,j in rect_ring(x,z,w*.5-t,d*.5-t,rr,n)])
    for a,b in zip(rows,rows[1:]):
        for j,A in enumerate(a):
            l=(j+1)%len(a);U=[A,a[l],b[l],b[j]];ps,no=zip(*U);g.quad(*ps,c,k,no)
    if cap:
        for row,ny in [(rows[0],-1),(rows[-1],1)]:
            for l,a in enumerate(row):g.tri(a[0],row[(l+1)%len(row)][0],(x,a[0][1],z),c,k,((0,ny,0),)*3)

def band_x(g,p,prof,c,k,n=40):
    x,y,z=p;u=[(math.sin(i*TAU/n),math.cos(i*TAU/n)) for i in range(n)]
    for (a,ra),(b,rb) in zip(prof,prof[1:]):
        gl=math.hypot(b-a,rb-ra)
        if gl<.0001:continue
        nx=(ra-rb)/gl;nr=(b-a)/gl
        for j,(s,t) in enumerate(u):
            s1,t1=u[(j+1)%n];na=(nx,nr*s,nr*t);nb=(nx,nr*s1,nr*t1)
            g.quad((x+a,y+ra*s,z+ra*t),(x+a,y+ra*s1,z+ra*t1),(x+b,y+rb*s1,z+rb*t1),(x+b,y+rb*s,z+rb*t),c,k,(na,nb,nb,na))

def quad_uv(g,p,uv,c,k,n):
    from geo import rgb
    c=rgb(c);nn=(n,)*4 if len(n)==3 and np.isscalar(n[0]) else n
    g.rows.extend((*p[i],*nn[i],*c,*uv[i],k) for i in (0,1,2,0,2,3))

CHARS="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?-:/;()&' "
FONTS=('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf')
G_SIZE=62;G_ATLAS=(G_SIZE*16,G_SIZE*15)

@lru_cache(maxsize=1)
def atlas():
    from PIL import Image,ImageFont,ImageDraw
    im=Image.new('L',G_ATLAS,0);d=ImageDraw.Draw(im)
    for style,font in enumerate(FONTS):
        f=ImageFont.truetype(font,45)
        for i,c in enumerate(CHARS):
            x0,y0=i%16*G_SIZE,(i//16+style*5)*G_SIZE
            a,b,c0,e=f.getbbox(c);d.text((x0+(G_SIZE-(c0-a))*.5-a,y0+G_SIZE*.51-22),c,font=f,fill=255,stroke_width=0)
    return im.tobytes()

def glyph_uv(ch,style=0,flip=False):
    i=CHARS.index(ch if ch in CHARS else '?');xx=i%16*G_SIZE;yy=(i//16+5*style)*G_SIZE;a,b=(xx+.5)/G_ATLAS[0],(xx+G_SIZE-.5)/G_ATLAS[0];c,d=(yy+.5)/G_ATLAS[1],(yy+G_SIZE-.5)/G_ATLAS[1]
    if flip:a,b=b,a
    return ((a,d),(b,d),(b,c),(a,c))

def letter(g,ch,pt,right,up,n,color,material=INK,style=0,flip=False):
    p=v(pt);r=v(right)*.5;u=v(up)*.5;quad_uv(g,(p-r-u,p+r-u,p+r+u,p-r+u),glyph_uv(ch,style,flip),color,material,n)

def line_of_text(g,text,p,size,spacing,col,style=0,top=True):
    x,y,z=p
    for j,c in enumerate(text):
        if c!=' ':letter(g,c,(x+spacing*(j-(len(text)-1)/2),y,z),(size,0,0),(0,0,-size) if top else (0,size,0),(0,1,0) if top else (0,0,1),col,INK,style)
