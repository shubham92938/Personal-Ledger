"""Self-contained world-space mesh and lens utilities for the canal-lock set."""
import math
from functools import lru_cache
import numpy as np

TAU=math.tau;I=np.eye(4,dtype='f4')

def v(p):return np.asarray(p,dtype='f4')
def norm(a):
    p=v(a);return p/max(1.e-10,float(np.linalg.norm(p)))
def clamp(x,a=0.,b=1.):return min(b,max(a,x))
def ease(x):
    t=clamp(x);return t*t*(3.-2.*t)
@lru_cache(maxsize=2048)
def _hex(c):
    c=c.lstrip('#');return tuple(int(c[i:i+2],16)/255. for i in (0,2,4))
def rgb(c):return _hex(c) if isinstance(c,str) else tuple(c)

def xform(pos=(0.,0.,0.),yaw=0.,pitch=0.,roll=0.,s=1.):
    cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pitch),math.sin(pitch);cr,sr=math.cos(roll),math.sin(roll)
    m=I.copy();m[:3,:3]=v(((cy,0,sy),(0,1,0),(-sy,0,cy)))@v(((1,0,0),(0,cp,-sp),(0,sp,cp)))@v(((cr,-sr,0),(sr,cr,0),(0,0,1)))*s;m[:3,3]=pos
    return m

def view(o,p):
    o=v(o);z=norm(o-v(p));x=norm((z[2],0,-z[0])) if abs(z[1])<.99999 else v((1,0,0));y=norm(np.cross(z,x));m=I.copy();m[:3,:3]=(x,y,z);m[:3,3]=-m[:3,:3]@o;return m

def perspective(fov,aspect,a=.1,b=1100.):
    q=1/math.tan(math.radians(fov)*.5)
    return v(((q/aspect,0,0,0),(0,q,0,0),(0,0,-(b+a)/(b-a),-2*b*a/(b-a)),(0,0,-1,0)))
def ortho(w,h,a=.1,b=390.):return v(((2/w,0,0,0),(0,2/h,0,0),(0,0,-2/(b-a),-(a+b)/(b-a)),(0,0,0,1)))

class Lens:
    def __init__(self,eye,target,fov,aspect=9/16):
        self.eye=v(eye);self.tar=self.target=v(target);self.fov=fov;self.ratio=aspect;self.v=view(eye,target);self.proj=perspective(fov,aspect);self.vp=self.proj@self.v
    def screen(self,p):
        q=self.vp@v((*p,1.));return (.5+.5*q[0]/q[3],.5-.5*q[1]/q[3])


class M:
    def __init__(self):self.rows=[]
    def tri(self,a,b,c,color,k=0,ns=None):
        if ns is None:
            n=norm(np.cross(v(b)-a,v(c)-a));ns=(n,n,n)
        s=rgb(color);self.rows.extend((*p,*n,*s,u,t,k) for p,n,(u,t) in zip((a,b,c),ns,((0,0),(1,0),(0,1))))
    def quad(self,a,b,c,d,color,k=0,ns=None):
        if ns is None:
            n=norm(np.cross(v(b)-a,v(c)-a));ns=(n,n,n,n)
        s=rgb(color);pts=(a,b,c,d);uv=((0,0),(1,0),(1,1),(0,1));self.rows.extend((*pts[i],*ns[i],*s,*uv[i],k) for i in (0,1,2,0,2,3))
    def box(self,p,d,color,k=0):
        # Centered dimensions along x/y/z. Per-face normals prevent unwanted smoothing.
        lo=np.array(p)-np.array(d)*.5;hi=np.array(p)+np.array(d)*.5
        a,b,c=lo;d,e,f=hi;q=self.quad
        q((a,b,c),(a,b,f),(a,e,f),(a,e,c),color,k,((-1,0,0),)*4);q((d,b,f),(d,b,c),(d,e,c),(d,e,f),color,k,((1,0,0),)*4)
        q((a,b,f),(a,b,c),(d,b,c),(d,b,f),color,k,((0,-1,0),)*4);q((a,e,c),(a,e,f),(d,e,f),(d,e,c),color,k,((0,1,0),)*4)
        q((d,b,c),(a,b,c),(a,e,c),(d,e,c),color,k,((0,0,-1),)*4);q((a,b,f),(d,b,f),(d,e,f),(a,e,f),color,k,((0,0,1),)*4)
    def sleeve(self,a,b,r,rr,color,k=0,n=12,cap=True):
        a,b=v(a),v(b);u=norm(b-a);s=norm((u[2],0,-u[0])) if abs(u[1])<.9999 else v((1,0,0));q=np.cross(u,s);slope=(r-rr)/max(.001,float(np.linalg.norm(b-a)))
        ring=[math.cos(i*TAU/n)*s+math.sin(i*TAU/n)*q for i in range(n)]
        ns=[norm(x+slope*u) for x in ring] if abs(slope)>1e-4 else ring
        for i in range(n):
            j=(i+1)%n;v0=ring[i];v1=ring[j];p=a+r*v0;q0=a+r*v1;q1=b+rr*v1;p1=b+rr*v0
            self.quad(p,q0,q1,p1,color,k,(ns[i],ns[j],ns[j],ns[i]))
            if cap:
                if r>.00001:self.tri(a,q0,p,color,k,(-u,)*3)
                if rr>.00001:self.tri(b,p1,q1,color,k,(u,)*3)
    def line(self,pts,r,col,k=0,n=8):
        for a,b in zip(pts,pts[1:]):
            if np.linalg.norm(np.subtract(a,b))>1e-6:self.sleeve(a,b,r,r,col,k,n,True)
    def lathe(self,profile,pos,color,k=0,n=22):
        x0,y0,z0=pos;p=profile
        u=[(math.cos(j*TAU/n),math.sin(j*TAU/n)) for j in range(n)]
        for (y,r),(h,s) in zip(p,p[1:]):
            d=math.hypot(h-y,s-r)
            if d<=1.e-7:continue
            ct,st=(h-y)/d,(r-s)/d
            for j,(a,b) in enumerate(u):
                c,e=u[(j+1)%n];ns=((ct*a,st,ct*b),(ct*c,st,ct*e))
                self.quad((x0+r*a,y0+y,z0+r*b),(x0+r*c,y0+y,z0+r*e),(x0+s*c,y0+h,z0+s*e),(x0+s*a,y0+h,z0+s*b),color,k,(ns[0],ns[1],ns[1],ns[0]))
    def ell(self,p,r,col,k=0,nu=18,nv=9):
        p=v(p);r=v(r);f=[];n=[]
        for j in range(nv+1):
            b=j*math.pi/nv;cb,sb=math.cos(b),math.sin(b);w=[v((sb*math.cos(i*TAU/nu),cb,sb*math.sin(i*TAU/nu))) for i in range(nu)]
            f.append([p+o*r for o in w]);n.append([norm(o/r) for o in w])
        for j in range(nv):
            for i in range(nu):
                l=(i+1)%nu;self.quad(f[j][i],f[j][l],f[j+1][l],f[j+1][i],col,k,(n[j][i],n[j][l],n[j+1][l],n[j+1][i]))
    def add(self,g,m=I):
        if m is I:self.rows.extend(g.rows);return
        a=np.asarray(g.rows,dtype='f4').reshape(-1,12).copy();a[:,:3]=a[:,:3]@m[:3,:3].T+m[:3,3];a[:,3:6]=a[:,3:6]@np.linalg.inv(m[:3,:3]);a[:,3:6]/=np.sqrt(np.maximum(1e-18,np.sum(a[:,3:6]**2,axis=1,keepdims=True)));self.rows.extend(a.tolist())
