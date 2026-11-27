"""Fast native-resolution PBR-inspired film stage with textured surfaces and directional shadows."""
import math
from functools import lru_cache
import numpy as np
from PIL import Image
import moderngl as gl
from geo import v,norm,ortho,view,rgb,I
from forge import atlas,G_ATLAS

@lru_cache(maxsize=1)
def texels():
    n=256;r=np.random.default_rng(5622692);X,Y=np.meshgrid(np.arange(n,dtype='f4')/n,np.arange(n,dtype='f4')/n)
    def tile(w,h=None):
        b=r.random((h or w,w),dtype='f4');return np.array(Image.fromarray(np.tile(b,(3,3))).resize((3*n,3*n),Image.Resampling.BICUBIC),dtype='f4')[n:2*n,n:2*n]-.5
    a,b,c,d,e=[tile(z) for z in (4,14,41,102,218)];k=tile(7,157);p=tile(22,183);h=Y+.025*np.sin(2*np.pi*X)+.026*tile(4,8);wood=np.sin(2*np.pi*(29*h+.64*k+.25*b));grain=.50+.128*wood+.28*k+.234*p+.167*a+.098*d-.083*np.maximum(0.,wood)**10
    f=(.51+.29*a+.23*b+.20*d,.52+.29*k+.19*b+.13*e,.52+.27*a+.38*d+.21*p,grain,.47+.19*a+.32*c+.32*e,.55+.19*a+.23*c+.25*d+.19*e,.5+.29*b+.34*c+.14*d,.5+.05*b,.47+.19*a+.17*b+.18*c+.24*d+.13*np.sin(X*TAU*103)*np.sin(Y*TAU*97),.52+.29*a+.23*c+.23*p,.47+.15*a+.32*b,.5+.1*c,.50+.27*a+.33*b+.20*c+.31*e,.52+.24*k+.26*d,.59+.32*k+.24*p,.52+.28*b)
    return (n,n,16),b''.join((np.clip(np.dstack((x,.55+.42*b+.13*d,.49+.26*c+.29*p)),0,1)*255).astype('u1').tobytes() for x in f)
TAU=math.tau
VS='''#version 330
in vec3 pos,nrm,col;in vec2 uv;in float mat_id;in vec4 ax,ay,az;
uniform mat4 vp,svp;uniform vec3 eye;uniform float time,sea;
out vec3 W,N,C,V,Sh;out vec2 T;flat out int K;
void main(){vec4 p=vec4(pos,1.);vec3 a=vec3(dot(ax,p),dot(ay,p),dot(az,p));vec3 n=vec3(dot(ax.xyz,nrm),dot(ay.xyz,nrm),dot(az.xyz,nrm));K=int(mat_id+.1);
 if(K==6 && n.y>.98 && sea>.001){float u=.69*a.x+.88*a.z-1.52*time;float v=.93*a.x-1.37*a.z+1.2*time; a.y+=sea*(sin(u)+.373*sin(v));n=vec3(-sea*(.69*cos(u)+.347*cos(v)),1.,-sea*(.88*cos(u)-.513*cos(v)));}
 W=a;N=n;C=col;V=eye-a;T=uv;Sh=(svp*vec4(a,1.)).xyz*.5+.5;gl_Position=vp*vec4(a,1.);}
'''
SV='''#version 330
in vec3 pos;in vec4 ax,ay,az;uniform mat4 svp;
void main(){vec4 p=vec4(pos,1.);gl_Position=svp*vec4(dot(ax,p),dot(ay,p),dot(az,p),1.);}
'''
FS='''#version 330
#extension GL_ARB_shader_image_load_store : require
layout(early_fragment_tests) in;
in vec3 W,N,C,V,Sh;in vec2 T;flat in int K;out vec4 O;
uniform sampler2DArray tex;uniform sampler2D glyph;uniform sampler2DShadow shad;
uniform vec3 sun,horizon;uniform float warm,time,flow,fog;
void main(){
 vec3 n=normalize(N),v=normalize(V),c=C;float l=max(0.,dot(n,sun));float sh=1.;
 if(K==10){O=vec4(c*(.81+.11*n.y)+vec3(.10,.105,.092),1.);return;}
 if(K==11){O=vec4(c*.968+vec3(.035,.046,.055),1.);return;}
 if(K==7){if(texture(glyph,T).r<.42)discard;O=vec4(c*(.78+.29*l),1.);return;}
 if(K==6){
  vec2 o=abs(n.y)>.70?W.xz:vec2(W.x+.39*W.z,W.y-.08*W.z);vec2 a=o*vec2(.33,.91)-vec2(time*.116*flow,time*.031);
  vec3 z=texture(tex,vec3(a,6.)).rgb;float ripple=.46+.36*z.r+.16*sin(25.1*a.x+17.*a.y+z.g*5.0);float b=1.-abs(dot(n,v));b*=b;
  float gloss=pow(max(0.,dot(n,normalize(v+sun))),18.);float veins=pow(max(0.,sin(16.2*a.x+17.5*a.y+7.2*z.g)),8.);
  vec3 g=c*(.74+.33*ripple)+(b*.097+gloss*.165+veins*(.024+.024*min(2.,abs(flow))))*vec3(.70,.91,1.0);
  O=vec4(clamp(mix(g,horizon,1.-exp(-fog*length(V)*.64)),0.,1.),1.);return;
 }
 vec3 a=texture(tex,vec3(T,float(K))).rgb;float t=a.r-.5;
 if(K==9){vec2 d=vec2(T.x,T.y)*vec2(.91,2.45);d.x+=mod(floor(d.y),2.)*.5;vec2 f=fract(d);float o=min(min(f.x,1.-f.x),min(f.y,1.-f.y));
 c*=mix(.59,.91+.17*fract(sin(dot(floor(d),vec2(21.27,91.19)))*3621.317),smoothstep(.008,.041,o+t*.032));}
 if(l>0.01&&Sh.x>.001&&Sh.x<.999&&Sh.y>.001&&Sh.y<.999)sh=texture(shad,vec3(Sh.xy,Sh.z-(.00050+.00156*(1.-l))));
 float d=.95+(.69 +.28*float(K==3||K==12))*t;
 float ref=float(K==1||K==2||K==13||K==14)*.83+float(K==0||K==4)*.22;
 float nv=dot(n,v);float edge=1.-max(0.,nv);float flare=0.;if(ref>.05||K==15){float h=max(0.,dot(n,sun)+nv)*inversesqrt(2.+2.*dot(v,sun));float q=h*h;float m=q*q;float n0=m*m;float pn=n0*n0;flare=pn*(.38+.62*pn);}
 float f=max(0.,dot(n,vec3(.548,.32,.773)));float oc=.88+.12*n.y;float shade=.74+.26*sh;
 vec3 amb=vec3(.295,.364,.45)*oc+vec3(.30,.237,.173)*f;
 vec3 lit=amb+vec3(1.39,1.21,.974)*l*sh*shade;
 vec3 color=c*c*d*lit;
 vec3 spec=vec3(.18,.192,.184)*(.32+.73*n.y*n.y);
 if(ref>.05){color+=ref*(.10+.46*flare)*spec*(.26+.47*l+.23*edge*edge);color+=ref*vec3(.12,.106,.075)*flare*sh;}
 if(K==15){color+=vec3(.067,.088,.094)*(.54+.37*edge+flare);}
 color*=vec3(1.+warm*.18,1.+warm*.049,1.-warm*.19);
 vec3 g=sqrt(clamp(color/(.91+.225*color),0.,1.));float ff=1.-exp(-fog*length(V));O=vec4(mix(g,horizon,ff),1.);
}
'''
BGV='''#version 330
out vec2 uv;void main(){vec2 p=vec2(gl_VertexID==1?3.:-1.,gl_VertexID==2?3.:-1.);uv=.5*p+.5;gl_Position=vec4(p,.999,1.);}
'''
BGF='''#version 330
in vec2 uv;out vec4 O;uniform vec3 zen,haze;uniform float tilt;
void main(){vec2 p=(uv-vec2(.44,.48));float f=smoothstep(-.16,.83,uv.y+tilt);float v=1.-.19*dot(p,p);O=vec4((mix(haze,zen,f)*v)+vec3(.019,.025,.025)*exp(-2.7*dot(p,p)),1.);}
'''

class Stage:
    def __init__(self,dims):
        g=gl.create_standalone_context(backend='egl',require=330);self.gl=g;self.p=g.program(vertex_shader=VS,fragment_shader=FS);self.sp=g.program(vertex_shader=SV,fragment_shader='#version 330\nvoid main(){}');self.b=g.program(vertex_shader=BGV,fragment_shader=BGF);self.ba=g.vertex_array(self.b,[]);self.fb={k:g.framebuffer([g.texture(d,4)],g.depth_renderbuffer(d)) for k,d in dims.items()}
        d=g.depth_texture((704,704));d.compare_func='<=';d.repeat_x=d.repeat_y=False;d.filter=(gl.LINEAR,gl.LINEAR);self.dep=d;self.df=g.framebuffer(depth_attachment=d)
        a,b=texels();self.tx=g.texture_array(a,3,b);self.tx.build_mipmaps();self.tx.filter=(gl.LINEAR_MIPMAP_NEAREST,gl.LINEAR)
        self.dt=g.texture(G_ATLAS,1,atlas());self.dt.build_mipmaps();self.dt.repeat_x=self.dt.repeat_y=False;self.dt.filter=(gl.LINEAR_MIPMAP_LINEAR,gl.LINEAR)
        self.tx.use(0);self.dt.use(1);d.use(2);self.p['tex']=0;self.p['glyph']=1;self.p['shad']=2;self.ref={};self.key=None;self.svp=None
    @staticmethod
    def mat(p,k,x):p[k].write(x.T.astype('f4',copy=False).tobytes())
    def mesh(self,m):
        k=id(m)
        if k in self.ref:return self.ref[k]
        a=np.ascontiguousarray(m.rows,'f4').copy();z=a.reshape(-1,3,12);norms=z[:,:,3:6].mean(1);axis=np.argmax(abs(norms),1);el=z[:,0,11].astype('i4');masks=el!=7
        scale=np.array([(1.28,1.6),(1.67,1.21),(1.42,1.44),(.174,.624),(1.,1.5),(.83,1.0),(1,1),(1,1),(.77,1.61),(1.64,2.17),(1,1),(1,1),(.56,.59),(1.2,1.1),(2.34,1.23),(1,1)],'f4')
        for i,x,y in ((0,2,1),(1,0,2),(2,0,1)):
            f=(axis==i)&masks;z[f,:,9]=z[f,:,x];z[f,:,10]=z[f,:,y]
        z[:,:,9:11]*=scale[el,None,:];a[a==0]=0;mn=a[:,:3].min(0);mx=a[:,:3].max(0);vec=(mx+mn)*.5;ext=(mx-mn)*.5
        _,ix,inv=np.unique(a.view(np.dtype((np.void,48))).ravel(),return_index=True,return_inverse=True)
        g=self.gl;idx=g.buffer(inv.astype('u4').tobytes());vb=g.buffer(a[ix].tobytes());ii=g.buffer(reserve=48*96,dynamic=True);itr=(ii,'4f 4f 4f /i','ax','ay','az');o=g.vertex_array(self.p,[(vb,'3f 3f 3f 2f 1f','pos','nrm','col','uv','mat_id'),itr],idx)
        z0=np.repeat(masks&(el!=6)&(el!=15),3);sub=g.buffer(inv[z0].astype('u4').tobytes()) if np.any(z0) else None;so=g.vertex_array(self.sp,[(vb,'3f 36x','pos'),itr],sub) if sub else None
        out=[m,vb,idx,sub,ii,o,so,None,vec,ext];self.ref[k]=out;return out
    def list(self,items,mtx,shadow=False):
        out={};ds={};rows=np.vstack([mtx[3]+s*mtx[i] for i in range(3) for s in (-1,1)]);d=rows[:,:3];e=np.abs(d)
        for m,xf,c in items:
            if shadow and not c:continue
            a=self.mesh(m);vex,ext=a[-2:];k=id(m)
            if xf is not I:vex=xf[:3,:3]@vex+xf[:3,3];ext=np.abs(xf[:3,:3])@ext
            # Water planes may displace in the shader; expand the clip tolerance a little.
            if np.any(d@vex+e@ext+rows[:,3]<-.4):continue
            if k not in out:out[k]=(a,[]);ds[k]=float(mtx[3,:3]@vex+mtx[3,3]-.2*np.linalg.norm(ext))
            out[k][1].append(xf[:3])
        return [out[k] for k in sorted(out,key=ds.get)] if not shadow else out.values()
    def draw(self,items,shadow=False):
        for b,a in items:
            va=b[6] if shadow else b[5]
            if va is None:continue
            if len(a)==1 and b[7] is a[0]:va.render(instances=1);continue
            arr=np.ascontiguousarray(a,'f4')
            for n in range(0,len(a),96):
                x=arr[n:n+96];raw=x.tobytes();ii=b[4]
                if not isinstance(b[7],bytes) or raw!=b[7]:ii.orphan();ii.write(raw);b[7]=raw
                va.render(instances=len(x))
    def shadow(self,s,f=0):
        if s.shadow is None:s.shadow=(tuple(s.lenses['short'].target),14.)
        center,width=s.shadow;key=(s.shot,tuple(center),width,s.sun,f//4)
        if key==self.key:return
        self.key=key;mid=v(center);l=norm(s.sun);mm=ortho(width,width,.12,width*3.6)@view(mid+l*width*1.29,mid);self.svp=mm
        g=self.gl;self.df.use();g.viewport=(0,0,*self.dep.size);self.df.clear(depth=1);g.enable_only(gl.DEPTH_TEST);g.depth_func='<';self.mat(self.sp,'svp',mm);self.mat(self.p,'svp',mm);self.draw(self.list(s.objects,mm,True),True)
    def frame(self,s,name):
        g=self.gl;p=self.p;b=self.b;l=s.lenses[name];f=self.fb[name];f.use();g.viewport=(0,0,*f.size);f.clear(0,0,0,1,depth=1);g.enable_only(0);b['tilt']=min(.32,max(-.28,float(l.eye[1]-l.tar[1])*.027));b['zen']=rgb(s.sky);b['haze']=rgb(s.horizon);self.ba.render(vertices=3);g.enable_only(gl.DEPTH_TEST);p['horizon']=rgb(s.horizon);p['warm']=s.warm;p['sun']=tuple(norm(s.sun));p['eye']=tuple(l.eye);p['time']=s.time;p['flow']=s.flow;p['fog']=s.fog;p['sea']=s.sea;self.mat(p,'vp',l.vp);self.draw(self.list(s.objects,l.vp));return f.read(components=4,alignment=1)
    def still(self,s,k):return Image.frombytes('RGBA',self.fb[k].size,self.frame(s,k)).transpose(Image.Transpose.FLIP_TOP_BOTTOM).convert('RGB')
