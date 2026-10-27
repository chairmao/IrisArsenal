"""064源曲面可见尺度：实际三角/UV/RGBA/渐变/源曲线采样，不以透明包围边角当主体。"""
from io import BytesIO
import math,numpy as np
from PIL import Image
from drive_effects059 import sample

def measure(a,meshes,tracks,blocks,duration,end):
    cache={}
    def tex(name,uv,clamp=False):
        if name not in cache:
            data=a.TEXTURES[name] if name in a.TEXTURES else (a.A/name).read_bytes()
            cache[name]=np.asarray(Image.open(BytesIO(data)).convert('RGBA'),float)/255
        im=cache[name];uv=np.clip(uv,0,1) if clamp else uv%1;x=uv[:,0]*(im.shape[1]-1);y=uv[:,1]*(im.shape[0]-1)
        i=x.astype(int);j=y.astype(int);u=(x-i)[:,None];v=(y-j)[:,None]
        return im[j,i]*(1-u)*(1-v)+im[j,np.minimum(i+1,im.shape[1]-1)]*u*(1-v)+im[np.minimum(j+1,im.shape[0]-1),i]*(1-u)*v+im[np.minimum(j+1,im.shape[0]-1),np.minimum(i+1,im.shape[1]-1)]*u*v
    # 36个确定性重心样本/三角；以真实投影面积加权，零alpha顶点与透明贴图边角不参与范围分母。
    bary=np.asarray([[u/8,v/8,1-(u+v)/8] for u in range(1,8) for v in range(1,9-u)])
    prepared=[]
    for mesh,tr in zip(meshes,tracks):
        p=(np.asarray(mesh['vertices'])@mesh['matrix'][:3,:3].T+mesh['matrix'][:3,3])@a.a.C.T*a.a.SCALE
        n=np.asarray(mesh['normals'])@np.linalg.inv(mesh['matrix'][:3,:3])@a.a.C.T;n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-9)
        idx=np.asarray(mesh['triangles']);uv=np.einsum('bc,fcd->fbd',bary,np.asarray(mesh['uv'])[idx]).reshape(-1,2)
        colours=np.asarray(mesh['colours']) if mesh['colours'] else np.ones((len(p),4))
        c=np.einsum('bc,fcd->fbd',bary,colours[idx]).reshape(-1,4)
        nn=np.einsum('bc,fcd->fbd',bary,n[idx]).reshape(-1,3);nn/=np.maximum(np.linalg.norm(nn,axis=1)[:,None],1e-9)
        prepared.append((p,idx,uv,c,nn,tr,a.MATS[a.material(mesh,blocks)]))
    bases=[];gold=math.pi*(3-math.sqrt(5))
    for k in range(12):
        y=1-2*(k+.5)/12;r=math.sqrt(1-y*y);f=np.array([r*math.cos(k*gold),y,r*math.sin(k*gold)]);right=np.cross(f,[0,1,0]);right/=np.linalg.norm(right);bases.append((f,np.stack([right,np.cross(right,f)])))
    snapshots=[]
    for t in np.linspace(.02,end,32):
        viewpoints=[[]for _ in bases];viewweights=[[]for _ in bases]
        for p,idx,uv,c,n,tr,d in prepared:
            st=sample(np.asarray(tr['frames']),float(t),duration);M=st[13:].reshape(3,4)
            if st[3]<.005:continue
            q=p@M[:,:3].T+M[:,3];points=np.einsum('bc,fcd->fbd',bary,q[idx]).reshape(-1,3)
            normal=n@np.linalg.inv(M[:,:3]);normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-9)
            face=np.cross(q[idx[:,1]]-q[idx[:,0]],q[idx[:,2]]-q[idx[:,0]])*.5
            tx=tex(d['diffuse'],uv*st[6:8]+st[4:6]) if d['has_source'] else np.ones((len(uv),4))
            vc=c.copy()
            if not d['vertex_color']:vc[:,:3]=1
            if not d['vertex_alpha']:vc[:,3]=1
            for vi,(f,base) in enumerate(bases):
                fade=np.ones(len(points))
                if d['use_falloff']:
                    a0,a1,a2,a3=st[9:13];u=np.clip((np.abs(normal@f)-a1)/max(1e-6,a0-a1),0,1);u=u*u*(3-2*u);fade=a3*(1-u)+a2*u
                rgb=tex(d['palette'],np.c_[tx[:,1],vc[:,1]*fade*st[0]],True)[:,:3] if d['grey_color'] else tx[:,:3]*vc[:,:3]*st[:3]
                alpha=tx[:,3]*vc[:,3]*fade*st[3]**2
                if d['grey_alpha']:alpha=tex(d['palette'],np.c_[tx[:,3],vc[:,3]*fade*st[3]**2],True)[:,3]
                # 只计可见alpha，按能量和面向相机的真实面积统计；不以整张贴图最大RGB虚报范围。
                w=alpha*np.maximum(0,rgb@np.array([.2126,.7152,.0722]))*st[8]*np.repeat(np.abs(face@f),len(bary))/len(bary)
                keep=(alpha>=.025)&(w>1e-10)
                viewpoints[vi].append(np.linalg.norm(points[keep]@base.T,axis=1));viewweights[vi].append(w[keep])
        radii=[];power=[]
        for rr,ww in zip(viewpoints,viewweights):
            if not rr or sum(len(x)for x in rr)==0:radii.append(0);power.append(0);continue
            r=np.concatenate(rr);w=np.concatenate(ww);ids=np.argsort(r);j=min(len(r)-1,np.searchsorted(np.cumsum(w[ids]),w.sum()*.95));radii.append(float(r[ids[j]]));power.append(float(w.sum()))
        snapshots.append({'age':float(t),'radius95_by_view':radii,'energy_area_by_view':power,'mean_power':float(np.mean(power))})
    peak=dict(max(snapshots,key=lambda x:x['mean_power']));assert min(peak['radius95_by_view'])>0
    # 完整时间序列供同一源实例的范围适配；不只看峰值而漏掉后期透明扩张。
    peak['time_series']=snapshots
    peak['method']='actual geometry/UV/texture/LUT/source colour and alpha squared/falloff; projected area and luminance weighted radius95, 12 views, 32 ages; CPU sampling, not GPU'
    return peak
