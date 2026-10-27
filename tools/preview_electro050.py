"""读取实际材质/网格/时间流，CPU复算像素混合和地面深度；不是游戏GPU截图。"""
import sys,json,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from safeio import ROOT,put
from scene_geometry import mesh
A=ROOT/'package/IrisArsenal/assets'
from test_drill_visibility import curves
doc=json.loads((ROOT/'docs/eight-effects.json').read_text('utf8'));fx=next(x for x in doc['assets'] if x['key']=='electro_area');parts=mesh(A/'iris_fx_electro_area.mesh');states,duration,bound=curves(A/'effect_curves.csv','electro_area')
W,H=600,480;scale=8;right=np.array([-1,0,0]);view=np.array([0,.6,-.8]);up=np.cross(view,right);transform=np.array([right,up,view]);origin=np.array([0,9,0]);textures={}
def tex(name,uv,clamp=False):
    if name not in textures:textures[name]=np.asarray(Image.open(A/name).convert('RGBA'),float)/255
    image=textures[name];uv=np.clip(uv,0,1) if clamp else uv%1
    # 双线性采样，保持真实alpha/梯度，不把整张图的RGB峰值当可见范围。
    x=uv[...,0]*(image.shape[1]-1);y=uv[...,1]*(image.shape[0]-1);i=x.astype(int);j=y.astype(int);u=(x-i)[...,None];v=(y-j)[...,None]
    return image[j,i]*(1-u)*(1-v)+image[j,np.minimum(i+1,image.shape[1]-1)]*u*(1-v)+image[np.minimum(j+1,image.shape[0]-1),i]*(1-u)*v+image[np.minimum(j+1,image.shape[0]-1),np.minimum(i+1,image.shape[1]-1)]*u*v

def attrs(part):
    # 此处实际FX固定48字节。vertex buffer来源由通用严格读取器验证，属性直接从独立消费者取。
    from test_drill_visibility import buffers
    data=next(p for n,p in buffers(A/'iris_fx_electro_area.mesh') if n==part['name'])
    return data[:,3:6].astype(float),data[:,6:10].astype(float),data[:,10:12].astype(float)

def frame(age,height):
    base=np.full((H,W,3),[.53,.36,.29]);accum=np.zeros_like(base);stats=[]
    idx=np.clip(age/duration*(states.shape[1]-1),0,states.shape[1]-1);lo=int(idx);hi=min(states.shape[1]-1,lo+1);values=states[:,lo]*(1-(idx-lo))+states[:,hi]*(idx-lo)
    for part,state in zip(parts,values):
        material=doc['materials'][part['name']];p=part['p'];normal,color,uv=attrs(part);matrix=state[13:].reshape(3,4)
        if material.get('burst_particle'):
            elapsed=age-color[:,0];life=color[:,1];t=np.clip(elapsed/np.maximum(.001,life),0,1);active=(elapsed>=0)&(elapsed<life)
            c0,c1,c2=np.array(material['colors']);x0,x1,x2,x3=material['intervals'];colour=np.broadcast_to(c1,(len(p),4)).copy()
            start=np.clip(t/max(.001,material['fade_in']),0,1);end=np.clip((t-(1-material['fade_out']))/max(.001,material['fade_out']),0,1)
            alpha=np.where(t<material['fade_in'],c0[3]*(1-start)+c1[3]*start,np.where(t>1-material['fade_out'],c1[3]*(1-end)+c2[3]*end,c1[3]))*active
            # shader原颜色RGB按intervals，alpha按单独fade，二者不能混在一起处理。
            f=np.clip((t-x0)/max(.001,x1-x0),0,1);g=np.clip((t-x2)/max(.001,x3-x2),0,1);colour=np.where((t<x1)[:,None],c0*(1-f[:,None])+c1*f[:,None],np.where((t<x2)[:,None],c1,c1*(1-g[:,None])+c2*g[:,None]));colour[:,3]=alpha
            size=np.interp(t,np.linspace(0,1,5),material['size_curve']);corner=(uv*2-1)*color[:,2,None]*size[:,None];cs=np.cos(color[:,3]);sn=np.sin(color[:,3]);corner=np.column_stack((cs*corner[:,0]-sn*corner[:,1],sn*corner[:,0]+cs*corner[:,1]))
            p=p+normal*np.maximum(elapsed,0)[:,None]+right*corner[:,0,None]+up*corner[:,1,None];normal=np.tile(view,(len(p),1));color=colour
        else:
            p=p@matrix[:,:3].T+matrix[:,3];normal=normal@np.linalg.inv(matrix[:,:3]);normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-9)
            if 'burst_card_center' in material:
                center=np.asarray(material['burst_card_center'])@matrix[:,:3].T+matrix[:,3];delta=p-center;p=center+delta[:,0,None]*right+delta[:,2,None]*up;normal=np.tile(view,(len(p),1))
        p=p*25+[0,height,0];screen=(p-origin)@transform.T;screen[:,:2]=screen[:,:2]*[scale,-scale]+[W/2,H/2];before=accum.sum()
        for tri in part['tri']:
            xy=screen[tri];low=np.maximum(0,np.floor(xy[:,:2].min(0)).astype(int));high=np.minimum([W-1,H-1],np.ceil(xy[:,:2].max(0)).astype(int))
            if np.any(high<low):continue
            x,y=np.meshgrid(np.arange(low[0],high[0]+1)+.5,np.arange(low[1],high[1]+1)+.5);a,b,c=xy;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(den)<1e-7:continue
            u=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den;v=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den;w=1-u-v;mask=(u>=0)&(v>=0)&(w>=0)
            def mix(data):return u[...,None]*data[tri[0]]+v[...,None]*data[tri[1]]+w[...,None]*data[tri[2]]
            pos=mix(p);mask&=pos[...,1]>=0 # 地面真正挡住地下像素，不能把地下包围计作看得见。
            tc=mix(uv);vertex=mix(color)
            if material.get('burst_particle'):
                texel=tex(material['texture'],tc);tint=np.asarray(material['base_color']);rgb=tex(material['palette'],np.stack((texel[...,1],vertex[...,1]*tint[0]),-1),True)[...,:3] if material['grey_color'] else texel[...,:3]*vertex[...,:3]*tint[:3]
                alpha=texel[...,3]*vertex[...,3]*tint[3]
                if material['grey_alpha']:alpha=tex(material['palette'],np.stack((texel[...,3],vertex[...,3]*tint[3]),-1),True)[...,3]*vertex[...,3]*tint[3]
                rgb*=material['gain'];cut=.002
            else:
                tc=tc*state[6:8]+state[4:6];texel=tex(material['diffuse'],tc) if material['has_source'] else np.ones((*u.shape,4));n=mix(normal);n/=np.maximum(np.linalg.norm(n,axis=-1)[...,None],1e-9)
                fade=np.ones_like(u)
                if material['use_falloff']:
                    f=state[9:13];width=f[0]-f[1];facing=np.abs(n@view);v0=np.clip((facing-f[1])/max(1e-5,width),0,1);v0=v0*v0*(3-2*v0);fade=f[3]*(1-v0)+f[2]*v0
                if not material['vertex_color']:vertex[...,:3]=1
                if not material['vertex_alpha']:vertex[...,3]=1
                rgb=tex(material['palette'],np.stack((texel[...,1],vertex[...,1]*fade*state[0]),-1),True)[...,:3] if material['grey_color'] else texel[...,:3]*vertex[...,:3]*state[:3]
                alpha=texel[...,3]*vertex[...,3]*fade*state[3]**2
                if material['grey_alpha']:alpha=tex(material['palette'],np.stack((texel[...,3],vertex[...,3]*fade*state[3]**2),-1),True)[...,3]
                rgb*=state[8];cut=material['alpha_cutoff']
            mask&=alpha>=cut;sl=(slice(low[1],high[1]+1),slice(low[0],high[0]+1));contribution=rgb*np.clip(alpha,0,1)[...,None];accum[sl][mask]+=contribution[mask]
        stats.append({'layer':part['name'],'daylight_additive_energy':float(accum.sum()-before)})
    # 与视频一致在明亮底色判断，而非黑底高增益假装明显；未模拟游戏完整后处理。
    out=Image.fromarray((np.clip(base+accum,0,1)*255).astype('uint8'));return out,stats,{'visible_pixel_count':int((accum.max(-1)>.03).sum()),'total_energy':float(accum.sum())}

def preview():
    out=Image.new('RGB',(4*600,2*500));report=[]
    from scene_geometry import actual_frames,rotation
    spec=next(x for x in json.loads((ROOT/'docs/eight-moves.json').read_text('utf8'))['moves'] if x['key']=='electro_cannon');ids,poses,_=actual_frames(A/'iris_action_electro_cannon_female.skeleton',spec);pose=poses[round(2.05/spec['duration']*(spec['frames']-1))];p,q=pose[ids['Bip01 Prop2']];
    import port_math as m
    q=m.qmul(q,m.axis((1,0,0),-90));height=float((np.asarray(p)+rotation(q)@np.array([1.807138657,0,8.534358047]))[1]);assert 0<height<25
    for row,height in enumerate((0,height)):
        for col,t in enumerate((.1,.25,.5,.8)):
            im,layers,stats=frame(t,height);ImageDraw.Draw(im).text((12,12),f'CPU / age {t} / center Y {height} / ground depth on',fill='white');out.paste(im,(col*600,row*500));report.append({'height':height,'time':t,**stats,'layers':layers})
    from io import BytesIO
    buf=BytesIO();out.save(buf,format='JPEG',quality=92);put(ROOT/'docs/previews050/electro-depth-before-after.jpg',buf.getvalue(),'源特效CPU像素/地面深度预览','同一真实网格/纹理/曲线，原脚底Y0与实际枪口高度对照；明亮底色，不靠黑底假装明显')
    put(ROOT/'docs/previews050/electro-depth-before-after.json',json.dumps({'rows':report,'method':'CPU shader math / actual materials and textures / ground depth / bright background','GPU_tested':False},ensure_ascii=False,indent=2),'CPU像素统计','记录每层实际像素贡献与地面遮挡；不是GPU/后处理/FPS结论');return report

if __name__=='__main__':preview()
