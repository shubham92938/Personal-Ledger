"""Cinematic stage for new episodes only: HDR lighting, physical finishes and a lens pass.

Geometry is still rendered at the two native delivery sizes. The small FX buffers
contain only glow, depth occlusion and haze, never the picture or caption plate.
"""
from pathlib import Path
from functools import lru_cache
import math
import numpy as np
from PIL import Image
import moderngl as gl
from stage_fast import Stage as Fast,VS,SV,BGV
from geo import rgb,norm,v,ortho,view,I
from forge import atlas,G_ATLAS

ROOT=Path(__file__).resolve().parent
# Geometry flags beyond the original sixteen materials.
OILED=16; CARD=17; SILK=18; PLASTER=19; YARN=20; OXIDE=21; GLINT=22; CERAMIC=23; CANVAS=24; RUST=25; STONECUT=26; PATTERN=27
UV_KEEP=(7,OILED,SILK,PATTERN)
SCALE=np.array([(1.12,1.77),(1.75,2.1),(1.21,1.4),(.31,.75),(1.0,1.5),(.8,1.0),(1,1),(1,1),(.91,1.91),(1.25,1.8),(1,1),(1,1),(.53,.64),(1.3,1.1),(1.75,1.29),(1,1),(1,1),(.78,.94),(1,1),(.48,.53),(1.21,1.63),(.89,1.42),(1,1),(1.49,1.19),(1.47,1.79),(.84,1.11),(.82,1.13),(1,1)],'f4')

@lru_cache(maxsize=1)
def surfaces():
    n=512;rng=np.random.default_rng(1839);x,y=np.meshgrid(np.arange(n,dtype='f4')/n,np.arange(n,dtype='f4')/n);tau=math.tau
    def noise(w,h=None):
        q=rng.random((h or w,w),dtype='f4');return np.array(Image.fromarray(np.tile(q,(3,3))).resize((n*3,n*3),Image.Resampling.BICUBIC),dtype='f4')[n:n*2,n:n*2]-.5
    a,b,c,d,e=[noise(k) for k in (5,16,53,149,353)];g,h,j=(noise(6,129),noise(14,57),noise(31,427))
    y1=y+.025*np.sin(tau*x)+.036*noise(4,6)+.021*g
    knots=[(.23,.33,.038,.062),(.69,.72,.053,.047),(.89,.18,.027,.031)]
    burr=x*0
    for u,vv,s,t in knots:
        dx=(x-u+.5)%1-.5;dy=(y-vv+.5)%1-.5;k=np.exp(-.26*((dx/s)**2+(dy/t)**2));y1+=.057*k*np.tanh(dy/t*1.4);burr+=.20*np.exp(-.60*((dx/(s*.75))**2+(dy/(t*.14))**2))+.095*k
    ring=np.sin(tau*(41*y1+.27*h));thin=np.maximum(0,ring)**10
    wood=.62+.15*a+.23*h+.26*g+.19*j-.15*thin-.64*burr
    height=.44+.19*g+.22*j-.12*thin-.52*burr
    # Fiber clusters and tiny voids, rather than identical stripes on every material.
    card=.64+.16*a+.18*b+.22*c+.16*d+.13*e+.27*noise(61,220)
    chalk=.55+.34*a+.29*b+.16*c+.19*d+.19*e
    linen=np.sin(tau*(163*x+.012*a))*np.sin(tau*(151*y+.019*a));canvas=.54+.17*a+.22*c+.14*e+.12*linen
    brushed=.53+.255*noise(310,16)+.16*b+.19*d
    leather=.58+.20*a+.25*c+.22*np.abs(d)*2+.24*e
    stone=.51+.29*a+.34*b+.31*c+.22*e
    ox=.46+.34*a+.31*b+.23*c+.20*d+.19*e
    s=[]
    def p(al,ht,rough):
        gx=(np.roll(ht,-1,axis=1)-np.roll(ht,1,axis=1))*2.4;gy=(np.roll(ht,-1,axis=0)-np.roll(ht,1,axis=0))*2.4
        s.append(np.uint8(np.clip(np.stack((al,.5+gx,.5+gy,rough+x*0),axis=2),0,1)*255).tobytes())
    for al,ht,ro in [(ox,ox,.56+b*.23),(brushed,brushed,.35+.27*b),(.58+b*.25+d*.26,brushed,.36+.29*b),(wood,height,.43+.26*b),(leather,leather,.65+.16*c),(stone,stone,.78+b*.15),(.56+.39*a+.23*h,.56+.39*a+.23*h,.21+b*.14),(.57+x*0,x*0,.61),(canvas,canvas,.75+b*.14),(stone,stone,.76+b*.17),(.56+.15*b,x*0,.21),(.58+x*0,x*0,.33),(stone,stone,.90+b*.15),(.59+.2*b+.23*d,brushed,.49+.18*b),(brushed,brushed,.24+.17*b),(.56+x*0,x*0,.53),(wood,height,.39+.29*b),(card,card,.81+b*.12),(.61+.13*b+.11*linen,canvas,.40+.12*b),(chalk,chalk,.83+.11*b),(canvas,canvas,.47+.12*b),(ox,ox,.57+.22*b),(.54+x*0,x*0,.46),(.56+.20*b+.26*d,leather,.31+.18*b),(canvas,canvas,.59+b*.21),(ox,ox,.72+.11*b),(stone,stone,.62+.21*b),(canvas,canvas,.59+.13*b)]:p(al,ht,ro)
    return (n,n,len(s)),b''.join(s)

FS=r'''#version 330
#extension GL_ARB_shader_image_load_store : require
layout(early_fragment_tests) in;
in vec3 W,N,C,V,Sh;in vec2 T;flat in int K;out vec4 O;
uniform sampler2DArray mats;uniform sampler2DShadow shad;uniform sampler2D glyph,portrait;
uniform vec3 sun,horizon,pract;
uniform float warm,time,flow,fog,shadowTex,windowed,key_power,fill_power,light_power,expose;
const vec3 FILL=vec3(.636,.44,.636);
const vec3 EDGE=vec3(.590,.239,-.771);
const vec3 BLUE=vec3(.60,.78,1.09);
const vec3 GOLD=vec3(1.0,.79,.54);
const float PI=3.14159265;
float sat(float x){return clamp(x,0.,1.);}
float sq(float x){return x*x;}
vec3 enc(vec3 x){return x*x;}
float shadow(float l){
 if(l<.006||min(Sh.x,Sh.y)<.002||max(Sh.x,Sh.y)>.998||Sh.z>=.999||Sh.z<=.001) return 1.;
 float dep=Sh.z-(.00031+.00080*(1.-l));vec2 t=vec2(shadowTex*1.57);vec2 a=Sh.xy;
 return .36*texture(shad,vec3(a,dep))+.16*(texture(shad,vec3(a+vec2(-.92,1.59)*t,dep))+texture(shad,vec3(a+vec2(1.78,.78)*t,dep))+texture(shad,vec3(a+vec2(.35,-1.83)*t,dep))+texture(shad,vec3(a+vec2(-1.58,-.72)*t,dep)));
}
float pane(vec3 p){
 float w=(-5.58-p.z)/min(-.05,sun.z);if(w<.0)return 1.;vec2 q=(p+sun*w).xy;
 float x=mod(q.x+1.6,3.2)-1.60;float h=q.y-4.04;float md=min(.73-abs(x),q.y-2.27);
 if(h>0.)md=min(md,.735-length(vec2(x,h)));float sub=max(0.,w)*.013+.025;
 float m=smoothstep(-sub,sub,md);
 m*=.62+.38*smoothstep(.015,.06+sub,abs(x));m*=.71+.29*smoothstep(.007,.035+sub,abs(mod(h+.255,.56)-.28));
 return m;
}
vec3 brdf(vec3 n,vec3 v,vec3 l,vec3 c,vec3 f0,float ro,float met,float vis){
 float nl=max(0.,dot(n,l));if(nl<.001||vis<.001)return vec3(0.);float nv=max(.025,dot(n,v));vec3 h=normalize(v+l);
 float nh=sat(dot(n,h)),hv=1.-sat(dot(h,v));
 float rr=sq(sq(ro));float z=nh*nh*(rr-1.)+1.;float d=rr/(PI*z*z+.0001);
 float k=sq(ro+1.)*.125;float g=nl/(nl*(1.-k)+k)*nv/(nv*(1.-k)+k);
 vec3 f=f0+(1.-f0)*sq(sq(hv))*hv;
 return vis*(c*(1.-met)*nl*(1.-f*.55)+min(d*g*.25/max(.024,nv),6.)*f);
}
void main(){
 vec3 n=normalize(N),v=normalize(V),c=enc(C);float dist=length(V),ef=1.-exp(-dist*fog);
 if(K==10){float veins=.84+.16*sin(35.*W.y+sin(W.x*16.)*.7);O=vec4(c*(2.1+.49*veins)+vec3(.81,1.16,1.39),1.);return;}
 if(K==11){O=vec4(c*4.+vec3(.92,.44,.12),1.);return;}
 if(K==22){O=vec4(c*(.82+.16*sin(time*1.1+W.y*5.7)),1.);return;}
 if(K==7){if(texture(glyph,T).r<.41)discard;O=vec4(c*(.42+.83*max(.05,dot(n,sun)))+.014,1.);return;}
 if(K==6){
  vec2 a=(abs(n.y)>.70?W.xz:vec2(W.x+.31*W.z,W.y)) *vec2(.33,1.03)-vec2(time*.101*flow,time*.040);
  vec4 pp=texture(mats,vec3(a,6.));float q=sin(35.*a.x+18.*a.y+5.*pp.r);n=normalize(n+vec3((pp.g-.5)*.5+q*.023,0.,(pp.b-.5)*.4));
  float fres=pow(1.-sat(abs(dot(v,n))),4.);float fl=sq(sq(sq(max(0.,dot(reflect(-sun,n),v)))));
  vec3 col=c*vec3(.41,1.07,1.23)*(.73+.53*pp.r)+vec3(.15,.31,.46)*fres+GOLD*fl*.28;
  O=vec4(mix(col,enc(horizon),ef*.48),1.);return;
 }
 vec2 uv=T;
 bool texuv=K==18||K==27;
 if(texuv)uv=T*vec2(3.88,4.90);
 vec4 g=texture(mats,vec3(uv,float(K)));float hot=(g.r-.55);
 if(texuv){vec3 art=texture(portrait,T).rgb;c=enc(art*C);}
 if(K==9){vec2 d=uv*vec2(.77,1.83);d.x+=mod(floor(d.y),2.)*.5;vec2 f=fract(d);float o=min(min(f.x,1.-f.x),min(f.y,1.-f.y));
   c*=mix(.47,.95+.10*fract(sin(dot(floor(d),vec2(21.27,91.19)))*3621.317),smoothstep(.006,.060,o+hot*.043));}
 float rough=clamp(g.a,.21,.95);
 float met=(K==1||K==14)?.88:K==2?.72:K==21?.32:K==13?.54:0.;
 float contrast=(K==16||K==3)?1.36:K==19?1.11:K==17?.97:.75;
 c*=clamp(1.+hot*contrast,.40,1.55);
 if(K==16||K==3)c*=vec3(1.+hot*.2,1.+hot*.05,1.-hot*.23);
 if(K==2||K==21||K==14){c*=mix(vec3(.46,.60,.64),vec3(1.1),smoothstep(.20,.62,g.r));}
 vec3 tan0=abs(n.y)>.90?vec3(1,0,0):normalize(vec3(n.z,0.,-n.x));
 vec3 bi=cross(n,tan0);float bump=K==14?.082:K==17?.25:K==16?.31:K==9?.25:K==19?.52:.29;
 n=normalize(n+bump*(tan0*(g.g-.5)+bi*(g.b-.5)));
 float nl=sat(dot(n,sun)),nv=sat(dot(n,v));float sh=shadow(nl);float patch=1.-windowed+windowed*(.24+.76*pane(W));
 vec3 rv=reflect(-v,n);float stripe=smoothstep(.15,.40,rv.y)*(.48+.52*smoothstep(-.32,.33,rv.z));float strip2=smoothstep(.74,.98,dot(rv,vec3(-.420,.460,-.775)));
 vec3 f0=mix(vec3(.034),c,met);
 if(K==16||K==3||K==23)f0+=vec3(.022);
 vec3 light=brdf(n,v,sun,c,f0,rough,met,sh*patch*key_power)*mix(vec3(1.02,1.10,1.23),vec3(1.13,.91,.66),warm);
 light+=brdf(n,v,FILL,c,f0,min(.91,rough+.12),met,fill_power)*GOLD;
 vec3 delta=pract-W;float len2=dot(delta,delta),bl=1./(1.+len2*.68);vec3 l=delta*inversesqrt(max(.002,len2));
 light+=brdf(n,v,l,c,f0,rough,met,bl*light_power)*vec3(1.0,.61,.30);
 light+=c*max(0.,dot(EDGE,n))*.15*BLUE;
 vec3 ambient=mix(vec3(.140,.119,.107),vec3(.18,.248,.305),sat(.5+.5*n.y));
 float fi=sq(sq(1.-nv));vec3 env=vec3(.08,.113,.145)+vec3(.22,.298,.33)*stripe+vec3(.48,.40,.25)*strip2;
 light+=c*ambient*(1.-met*.67)+env*(f0*(.24+met*.56+(1.-rough)*.62)+fi*.035);
 if(K==18||K==20||K==24||K==27){
   float fid=abs(dot(tan0,normalize(v+sun)));float sheen=sq(sq(1.-fid));
   light+=vec3(.48,.52,.54)*((.073*fi+.186*sheen*nl)*sh*patch+.03*stripe)*mix(vec3(.80),sqrt(c),.30);
 }
 if(K==15)light+=vec3(.086,.106,.114);
 O=vec4(expose*mix(light,enc(horizon)*.46,ef),1.);
}
'''

SKY=r'''#version 330
in vec2 uv;out vec4 O;uniform vec3 zen,haze;uniform float tilt;
void main(){vec2 p=uv-vec2(.51,.50);float t=smoothstep(-.2,.88,uv.y+tilt);vec3 a=mix(haze,zen,t);O=vec4(a*a*(.77+.28*exp(-dot(p,p)*3.8)),1.);}
'''

FX=r'''#version 330
in vec2 uv;out vec4 O;
uniform sampler2D col,dep;
uniform vec2 inv;
uniform vec3 eye;
uniform mat3 rays;
uniform float shaft,window_distance;
float z(vec2 at){return .1/max(.0000909,1.-texture(dep,at).r*.99990909);}
vec3 hi(vec2 at){vec3 v=texture(col,at).rgb;return min(max(v-vec3(.65),0.),vec3(3.));}
float window_volume(vec3 p){
 // Sun enters the tall west windows and spreads into the enclosed room.
 float d=max(0.,p.z-window_distance);vec2 q=p.xy+vec2(-.69,.55)*d;float x=mod(q.x+1.6,3.2)-1.60;float h=max(0.,q.y-4.04);float s=.10+.068*d;
 float m=(1.-smoothstep(.55-s,.72+s,length(vec2(x,h))))*smoothstep(2.42-s,2.60+s,q.y);
 return m*exp(-.17*d)*smoothstep(-.2,.45,d);
}
void main(){
 float z0=z(uv);vec2 v=inv*2.0;float a=0.;float r=clamp(7.6/z0,.22,2.);
 const vec2 x[6]=vec2[6](vec2(1.,.13),vec2(.46,.79),vec2(-.67,.70),vec2(-1.,-.22),vec2(-.35,-.89),vec2(.64,-.72));
 if(z0<100.){for(int i=0;i<6;i++){float d=z0-z(uv+x[i]*v*r*4.1);a+=smoothstep(.013,.14,d)*(1.-smoothstep(.19,.77,d));}}
 vec2 k=v*4.2;
 vec3 color=hi(uv)*.22+(hi(uv+vec2(k.x,k.y*.38))+hi(uv+vec2(-k.x,k.y*.38))+hi(uv+vec2(k.x*.23,-k.y))+hi(uv+vec2(-k.x*.23,k.y)))*.124;
 color+=(hi(uv+k*1.73)+hi(uv-k*1.73))*.105;
 if(shaft>.002){
   vec3 dir=rays*vec3(uv*2.-1.,1.);
   float m=min(16.,z0);float f=(window_volume(eye+dir*m*.30)*.30+window_volume(eye+dir*m*.59)*.43+window_volume(eye+dir*m*.83)*.27);
   color+=m*f*shaft*vec3(.64,.52,.37)/.069;
 }
 O=vec4(color,1.-.29*min(1.,a*.222));
}
'''

FINISH=r'''#version 330
in vec2 uv;out vec4 O;
uniform sampler2D col,dep,fx;
uniform vec2 inv;
uniform float focus,aperture,time;
float z(vec2 at){return .1/max(.0000909,1.-texture(dep,at).r*.99990909);}
vec3 color(vec2 at){return texture(col,at).rgb;}
float Y(vec3 c){return dot(c,vec3(.2126,.7152,.0722));}
vec3 ag(vec3 x){return clamp(x*(2.51*x+.03)/(x*(2.43*x+.59)+.14),0.,1.);}

void main(){
 float d=z(uv);vec3 c=color(uv);vec4 ef=texture(fx,uv);
 float b=clamp(abs(1./max(.16,d)-1./focus)*aperture-.24,0.,16.);vec2 r=inv*b;
 if(b>.82){
   vec2 a=uv+r*vec2(.92,.07);vec2 p=uv+r*vec2(-.59,.77);vec2 q=uv+r*vec2(-.47,-.85);vec2 s=uv+r*vec2(.42,.58);vec2 t=uv+r*vec2(.34,-.54);vec2 f=uv+r*vec2(-.73,.13);
   vec3 mix0=(color(a)+color(p)+color(q)+color(s)+color(t)+color(f))*.144+c*.136;
   c=mix(c,mix0,smoothstep(.82,2.45,b));
 }else{
   // A small native-pixel contour filter. No softening of detailed texture interiors.
   vec3 a=color(uv+vec2(inv.x,0)),q=color(uv-vec2(inv.x,0)),b0=color(uv+vec2(0,inv.y)),t=color(uv-vec2(0,inv.y));
   float dx=abs(Y(a)-Y(q)),dy=abs(Y(b0)-Y(t));float s0=smoothstep(.018,.17,max(dx,dy))*.29;
   c=mix(c,dx>dy?(a+q)*.5:(b0+t)*.5,s0);
 }
 c*=mix(ef.a,1.,smoothstep(2.0,7.,b));
 c+=ef.rgb*.069;

 vec2 pp=uv-.5;float vign=1.-.33*dot(pp,pp);
 c=ag(c*vign);c=mix(c,vec3(Y(c)),.043);
 c=sqrt(max(c,0.));
 float grit=fract(52.9829189*fract(dot(gl_FragCoord.xy+floor(time*24.)*vec2(17.23,9.7),vec2(.06711056,.00583715))))-.5;
 O=vec4(clamp(c+grit*.007,0.,1.),1.);
}
'''

class Stage(Fast):
    def __init__(self,dims):
        g=gl.create_standalone_context(backend='egl',require=330);self.gl=g
        self.p=g.program(vertex_shader=VS,fragment_shader=FS);self.sp=g.program(vertex_shader=SV,fragment_shader='#version 330\nvoid main(){}')
        self.b=g.program(vertex_shader=BGV,fragment_shader=SKY);self.ba=g.vertex_array(self.b,[])
        self.f=g.program(vertex_shader=BGV,fragment_shader=FX);self.fa=g.vertex_array(self.f,[])
        self.post=g.program(vertex_shader=BGV,fragment_shader=FINISH);self.pa=g.vertex_array(self.post,[])
        self.target={};self.fb={}
        for k,d in dims.items():
            a=g.texture(d,4,dtype='f2');z=g.depth_texture(d);z.compare_func='';z.filter=(gl.NEAREST,gl.NEAREST)
            hf=g.texture((max(2,d[0]//3),max(2,d[1]//3)),4,dtype='f2');out=g.texture(d,4)
            for tex in (a,z,hf,out):tex.repeat_x=tex.repeat_y=False
            self.target[k]=(a,z,g.framebuffer([a],z),hf,g.framebuffer([hf]));self.fb[k]=g.framebuffer([out])
        d=g.depth_texture((1280,1280));d.compare_func='<=';d.repeat_x=d.repeat_y=False;d.filter=(gl.LINEAR,gl.LINEAR);self.dep=d;self.df=g.framebuffer(depth_attachment=d)
        a,b=surfaces();self.tx=g.texture_array(a,4,b);self.tx.build_mipmaps();self.tx.filter=(gl.LINEAR_MIPMAP_LINEAR,gl.LINEAR)
        self.dt=g.texture(G_ATLAS,1,atlas());self.dt.build_mipmaps();self.dt.repeat_x=self.dt.repeat_y=False;self.dt.filter=(gl.LINEAR_MIPMAP_LINEAR,gl.LINEAR)
        p=ROOT/'assets'/'jacquard-silk.png'
        im=Image.open(p).convert('RGB').transpose(Image.Transpose.FLIP_TOP_BOTTOM) if p.exists() else Image.new('RGB',(2,2),'#ccc1a3')
        self.art=g.texture(im.size,3,im.tobytes(),alignment=1);self.art.build_mipmaps();self.art.repeat_x=self.art.repeat_y=False;self.art.filter=(gl.LINEAR_MIPMAP_LINEAR,gl.LINEAR)
        self.tx.use(0);self.dt.use(1);d.use(2);self.art.use(3)
        for k,i in {'mats':0,'glyph':1,'shad':2,'portrait':3}.items():self.p[k]=i
        for p in (self.f,self.post):p['col']=4;p['dep']=5
        self.post['fx']=6;self.p['shadowTex']=1./d.size[0];self.ref={};self.key=None;self.svp=None

    def mesh(self,m):
        k=id(m)
        if k in self.ref:return self.ref[k]
        a=np.ascontiguousarray(m.rows,'f4').copy();z=a.reshape(-1,3,12);axis=np.argmax(abs(z[:,:,3:6].mean(1)),1);el=z[:,0,11].astype('i4');masked=~np.isin(el,UV_KEEP)
        for i,x,y in ((0,2,1),(1,0,2),(2,0,1)):
            f=(axis==i)&masked;z[f,:,9]=z[f,:,x];z[f,:,10]=z[f,:,y]
        z[:,:,9:11]*=SCALE[el,None,:];a[a==0]=0;mn=a[:,:3].min(0);mx=a[:,:3].max(0);vec=(mx+mn)*.5;ext=(mx-mn)*.5
        _,ix,inv=np.unique(a.view(np.dtype((np.void,48))).ravel(),return_index=True,return_inverse=True)
        g=self.gl;idx=g.buffer(inv.astype('u4').tobytes());vb=g.buffer(a[ix].tobytes());ii=g.buffer(reserve=48*96,dynamic=True);itr=(ii,'4f 4f 4f /i','ax','ay','az');o=g.vertex_array(self.p,[(vb,'3f 3f 3f 2f 1f','pos','nrm','col','uv','mat_id'),itr],idx)
        z0=np.repeat(~np.isin(el,(6,7,10,11,15,22)),3);sub=g.buffer(inv[z0].astype('u4').tobytes()) if np.any(z0) else None;so=g.vertex_array(self.sp,[(vb,'3f 36x','pos'),itr],sub) if sub else None
        out=[m,vb,idx,sub,ii,o,so,None,vec,ext];self.ref[k]=out;return out

    def shadow(self,s,f=0):
        center,width=s.shadow or (tuple(s.lenses['short'].target),16.)
        key=(s.shot,tuple(center),width,s.sun,f//2)
        if key==self.key:return
        self.key=key;mid=v(center);l=norm(s.sun);mm=ortho(width,width,.12,width*3.6)@view(mid+l*width*1.29,mid);self.svp=mm
        g=self.gl;self.df.use();g.viewport=(0,0,*self.dep.size);self.df.clear(depth=1);g.enable_only(gl.DEPTH_TEST);g.depth_func='<';self.mat(self.sp,'svp',mm);self.mat(self.p,'svp',mm);self.draw(self.list(s.objects,mm,True),True)

    def frame(self,s,name):
        g=self.gl;p=self.p;b=self.b;l=s.lenses[name];f=self.fb[name];a,z,viewfb,hf,fx=self.target[name];w,h=f.size;viewfb.use();g.viewport=(0,0,w,h);viewfb.clear(0,0,0,1,depth=1)
        g.enable_only(0);b['tilt']=min(.32,max(-.28,float(l.eye[1]-l.tar[1])*.039));b['zen']=rgb(s.sky);b['haze']=rgb(s.horizon);self.ba.render(vertices=3)
        g.enable_only(gl.DEPTH_TEST);meta=s.attributes.get('light',{});p['horizon']=rgb(s.horizon);p['warm']=s.warm;p['sun']=tuple(norm(s.sun));p['eye']=tuple(l.eye);p['time']=s.time;p['flow']=s.flow;p['fog']=s.fog;p['sea']=s.sea
        for k,val in dict(windowed=.0,pract=(-3.8,4.0,-.3),key_power=1.48,fill_power=.32,light_power=.62,expose=1.0).items():p[k]=meta.get(k,val)
        self.mat(p,'vp',l.vp);self.draw(self.list(s.objects,l.vp))
        a.use(4);z.use(5);hf.use(6);g.enable_only(0);fx.use();g.viewport=(0,0,*fx.size);p=self.f;p['inv']=(1./w,1./h);p['eye']=tuple(l.eye);p['shaft']=meta.get('shaft',0.);p['window_distance']=meta.get('window_z',-5.58)
        R=l.v[:3,:3].T@np.diag([1./l.proj[0,0],1./l.proj[1,1],-1.]);self.mat(p,'rays',R);self.fa.render(vertices=3)
        f.use();g.viewport=(0,0,w,h);p=self.post;p['inv']=(1./w,1./h);p['focus']=float(meta.get('focus_'+name,np.linalg.norm(l.eye-l.tar)));p['aperture']=meta.get('aperture',22.)*min(w,h)/1080.
        # STRESS-TEST FIX (F1): V5's stable-grain patch removed the FINISH
        # shader's only use of `time`, so the uniform is inactive and assigning
        # it raised KeyError on every frame. Guard the assignment; V3/V4 keep
        # the animated grain, V5/V6 intentionally freeze it.
        try:p['time']=s.time
        except KeyError:pass
        self.pa.render(vertices=3)
        return f.read(components=4,alignment=1)
