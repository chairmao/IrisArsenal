"""041只读真实粒子/图集/LUT计算主体可见尺度；不从录像像素推算游戏距离。"""
import math
from io import BytesIO
import numpy as np
from PIL import Image

def samples(a,d,age,life,cache):
    # 与已部署IrisBurstVP/FP相同的寿命alpha、矩形图集帧间插值及调色alpha。
    t=age/life;c=np.asarray(d['colors']);fi,fo=d['fade_in'],d['fade_out']
    alpha=np.interp(t,[0,fi],[c[0,3],c[1,3]]) if t<fi else np.interp(t,[1-fo,1],[c[1,3],c[2,3]]) if t>1-fo else c[1,3]
    def image(name):
        if name not in cache:cache[name]=np.asarray(Image.open(BytesIO(a.TEXTURES[name])).convert('RGBA'),float)/255
        return cache[name]
    src=image(d['texture']);lut=image(d['palette']);cols,rows,count=d.get('atlas_grid',[d['atlas'],d['atlas'],d['atlas']**2])
    grid=(np.arange(20)+.5)/20;u,v=np.meshgrid(grid,grid);uv=np.c_[u.ravel(),v.ravel()]
    f=t*(count-1);lo=int(f);hi=min(count-1,lo+1)
    def frame(n):
        q=(uv+[n%cols,n//cols])/np.array([cols,rows]);q=q*np.asarray(d['uv'][2:])+d['uv'][:2]
        ix=(q[:,0]%1*src.shape[1]).astype(int);iy=(q[:,1]%1*src.shape[0]).astype(int)
        return src[iy,ix]
    tex=frame(lo)*(1-(f-lo))+frame(hi)*(f-lo);out=tex[:,3]*alpha*d['base_color'][3]
    if d['grey_alpha']:
        iy=min(lut.shape[0]-1,max(0,int(alpha*d['base_color'][3]*lut.shape[0])));ix=np.clip((tex[:,3]*lut.shape[1]).astype(int),0,lut.shape[1]-1)
        out=lut[iy,ix,3]*alpha*d['base_color'][3]
    gamma,gain=d.get('profile',[1,1])[:2];out=np.minimum(1,np.maximum(out,0)**gamma*gain)
    active=out>=.025
    return uv[active]*2-1,out[active]

def measure(a,layers,times):
    # 12个固定方向是数据投影基底；同一基底比较两份真实资产，不借录像估镜头/距离。
    bases=[];gold=math.pi*(3-math.sqrt(5));cache={};snapshots=[]
    for n in range(12):
        y=1-2*(n+.5)/12;r=math.sqrt(1-y*y);f=np.array([r*math.cos(n*gold),y,r*math.sin(n*gold)])
        right=np.cross(f,[0,1,0]);right/=np.linalg.norm(right);bases.append(np.stack([right,np.cross(right,f)]))
    for age in times:
        points=[];weights=[];power=0
        for l in layers:
            d=a.MATS[l['material']]
            for p in l['particles']:
                dt=age-p[6]
                if not 0<=dt<p[7]:continue
                uv,w=samples(a,d,dt,p[7],cache)
                if not len(w):continue
                size=p[8]*np.interp(dt/p[7],np.linspace(0,1,5),l['size_curve']);cs,sn=math.cos(p[9]),math.sin(p[9]);xy=uv@np.array([[cs,sn],[-sn,cs]])*size
                center=np.asarray(p[:3])+np.asarray(p[3:6])*dt+.5*np.asarray(l.get('acceleration',[0,0,0]))*dt*dt
                points.append((center,xy));weights.append(w*size*size);power+=float(w.sum()*size*size)
        if power==0:continue
        weight=np.concatenate(weights);radii=[]
        for base in bases:
            radius=np.concatenate([np.linalg.norm(xy+base@center,axis=1) for center,xy in points]);order=np.argsort(radius)
            index=np.searchsorted(np.cumsum(weight[order]),weight.sum()*.95);radii.append(float(radius[order[min(index,len(order)-1)]]))
        snapshots.append({'age':float(age),'visible_area_proxy':power,'radius95_by_view':radii})
    assert snapshots
    # 取主体可见面积峰值，而非少数火星/透明尾部的最远一角；95%按真实alpha和面积加权。
    return max(snapshots,key=lambda s:s['visible_area_proxy'])

def calibrate(a,layers,tracks,duration,start,profile):
    fire=[l for l in layers if l['name'].startswith('FlamesTall03')];assert len(fire)==7
    # 主火浪网格有效窗由实际颜色/alpha轨道给出，不能用长达6.5秒的透明尾扩大归一分母。
    states=np.asarray(tracks[0]['frames']);energy=np.max(states[:,:3],axis=1)*states[:,3]*states[:,8]
    last=np.flatnonzero(energy>=energy.max()*.1)[-1];end=duration*last/(len(states)-1)
    before=measure(a,fire,np.linspace(start+.05,start+end,28))
    if profile=='drill':
        import drill_volume
        blue,_=drill_volume.build(a);reference=measure(a,blue,np.linspace(.04,.45,24));target=np.asarray(reference['radius95_by_view'])*.75
        scale=max(target/np.asarray(before['radius95_by_view']))
    else:
        # 翻滚的主爆炸可见半径按本次已有伤害球的单位半径1校准，不改R24伤害。
        reference={'radius95_by_view':[1.]*12,'unit':'existing blast radius'};scale=max(1/np.asarray(before['radius95_by_view']))
    assert 1<=scale<=16,(profile,scale)
    return float(scale),{'profile':profile,'method':'source mesh bright window; source flame particles only; actual texture/LUT alpha>=0.025; opacity-area weighted radius95 at visible-area peak; 12 fixed data views','source_body_window':[0,float(end)],'before':before,'reference':reference,'required_ratio':.75 if profile=='drill' else 1.,'uniform_scale':float(scale),'after_radius95_by_view':(np.asarray(before['radius95_by_view'])*scale).tolist(),'video_pixel_measurement':False,'damage_changed':False,'GPU_measurement':False}
