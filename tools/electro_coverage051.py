"""051按真实源三角面、UV/调色和透明度测量发亮主体；不拿透明几何外缘缩小火焰。"""
from io import BytesIO
import math
import numpy as np
from PIL import Image

def sample(image,uv,clamp=False):
    uv=np.clip(uv,0,1) if clamp else uv%1
    x=uv[...,0]*(image.shape[1]-1);y=uv[...,1]*(image.shape[0]-1);ix=x.astype(int);iy=y.astype(int);u=(x-ix)[...,None];v=(y-iy)[...,None]
    return image[iy,ix]*(1-u)*(1-v)+image[iy,np.minimum(ix+1,image.shape[1]-1)]*u*(1-v)+image[np.minimum(iy+1,image.shape[0]-1),ix]*(1-u)*v+image[np.minimum(iy+1,image.shape[0]-1),np.minimum(ix+1,image.shape[1]-1)]*u*v

def measure(e,meshes,blocks,timeline):
    # 固定均匀三角采样和12个空间投影，测量实际纹理发亮面积；不从视频像素猜游戏单位。
    # 颜色/alpha/UV/falloff仍逐帧取源数据，只统一整套效果尺度，不改变源形状、出生和色彩。
    rng=np.random.default_rng(510051);uv0=rng.random((64,2));uv0[uv0.sum(1)>1]=1-uv0[uv0.sum(1)>1];bary=np.c_[1-uv0.sum(1),uv0];sources=[];cache={}
    def image(name):
        if name not in cache:cache[name]=np.asarray(Image.open(BytesIO(e.TEXTURES[name])).convert('RGBA'),float)/255
        return cache[name]
    for mesh,track in zip(meshes,timeline['tracks']):
        mat=e.MATS[e.material(mesh,blocks)];tri=np.asarray(mesh['triangles']);p=(np.asarray(mesh['vertices'])@mesh['matrix'][:3,:3].T+mesh['matrix'][:3,3])@e.a.C.T*e.a.SCALE
        n=np.asarray(mesh['normals'])@np.linalg.inv(mesh['matrix'][:3,:3])@e.a.C.T;n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-9)
        rgba=np.asarray(mesh['colours'] or [[1,1,1,1]]*len(p));texuv=np.asarray(mesh['uv']);surface=[]
        for values in (p,n,rgba,texuv):surface.append(np.einsum('sj,tjk->tsk',bary,values[tri]).reshape(-1,values.shape[1]))
        sources.append((mesh,mat,track,tri,p,*surface))
    views=[];gold=math.pi*(3-math.sqrt(5))
    for i in range(12):
        y=1-2*(i+.5)/12;r=math.sqrt(1-y*y);f=np.array([r*math.cos(i*gold),y,r*math.sin(i*gold)]);right=np.cross(f,[0,1,0]);right/=np.linalg.norm(right);views.append((f,right,np.cross(right,f)))
    rows=[]
    for time in np.linspace(.033333,.8,24):
        radius=[];powers=[]
        for view,right,up in views:
            points=[];weights=[]
            for mesh,mat,track,tri,vertices,p,n,color,uv in sources:
                frames=np.asarray(track['frames']);x=time/timeline['duration']*(len(frames)-1);lo=int(x);hi=min(len(frames)-1,lo+1);state=frames[lo]*(1-(x-lo))+frames[hi]*(x-lo);M=state[13:].reshape(3,4)
                q=p@M[:,:3].T+M[:,3];nn=n@np.linalg.inv(M[:,:3]);nn/=np.maximum(np.linalg.norm(nn,axis=1)[:,None],1e-9)
                vv=vertices@M[:,:3].T+M[:,3];cross=np.cross(vv[tri[:,1]]-vv[tri[:,0]],vv[tri[:,2]]-vv[tri[:,0]])
                area=np.repeat(abs(cross@view)/2/64,64)
                if mesh['name']=='Glow:0':
                    center=(vv.min(0)+vv.max(0))*.5;delta=q-center;q=center+delta[:,0,None]*right+delta[:,2,None]*up;nn=np.tile(view,(len(q),1));area=np.repeat(np.linalg.norm(cross,axis=1)/2/64,64)
                tex=sample(image(mat['diffuse']),uv*state[6:8]+state[4:6]) if mat['has_source'] else np.ones((len(q),4));vc=color.copy()
                if not mat['vertex_color']:vc[:,:3]=1
                if not mat['vertex_alpha']:vc[:,3]=1
                fade=np.ones(len(q))
                if mat['use_falloff']:
                    f=state[9:13];u=np.clip((abs(nn@view)-f[1])/max(1e-5,f[0]-f[1]),0,1);u=u*u*(3-2*u);fade=f[3]*(1-u)+f[2]*u
                rgb=sample(image(mat['palette']),np.c_[tex[:,1],vc[:,1]*fade*state[0]],True)[:,:3] if mat['grey_color'] else tex[:,:3]*vc[:,:3]*state[:3]
                alpha=tex[:,3]*vc[:,3]*fade*state[3]**2
                if mat['grey_alpha']:alpha=sample(image(mat['palette']),np.c_[tex[:,3],vc[:,3]*fade*state[3]**2],True)[:,3]
                energy=(rgb@np.array([.2126,.7152,.0722]))*np.clip(alpha,0,1)*state[8];active=(alpha>=max(.025,mat['alpha_cutoff']))&(energy>.01)
                points.append(q[active]);weights.append((area*energy)[active])
            q=np.concatenate(points);w=np.concatenate(weights)
            if w.sum()<=0:radius.append(0);powers.append(0);continue
            r=np.linalg.norm(np.c_[q@right,q@up],axis=1);ix=np.argsort(r);at=np.searchsorted(np.cumsum(w[ix]),w.sum()*.95);radius.append(float(r[ix[min(at,len(ix)-1)]]));powers.append(float(w.sum()))
        rows.append({'time':float(time),'radius95_by_view':radius,'visible_area_energy_by_view':powers})
    peak=max(rows,key=lambda x:sum(x['visible_area_energy_by_view']));reference=max(peak['radius95_by_view']);assert reference>0
    return reference,{'method':'64 deterministic barycentric samples per source triangle; actual UV/RGBA/LUT/falloff; opacity>=0.025; area-energy weighted visible radius95; peak visible-area time; 12 views','reference_radius':reference,'peak':peak,'rows':rows,'source_layers':[m['name'] for m in meshes],'added_textures':False,'geometry_rearranged':False,'GPU_tested':False}
