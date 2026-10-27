"""051真实序列化资源CPU预览；明亮底色，不编译Shader，不冒充游戏截图。"""
from pathlib import Path
from io import BytesIO
import json,math,sys
import numpy as np
from PIL import Image,ImageDraw
from safeio import ROOT,put
from test_drill_visibility import buffers,curves
from electro_coverage051 import sample
GAME=Path('D:/steam/steamapps/common/Kenshi/mods/IrisArsenal');A=ROOT/'package/IrisArsenal/assets'

def muzzle_frame(assets,materials,time,native_fade):
    # 直接读52字节实际顶点，不用作者JSON的位置/半径代替最终产物。
    W,H=560,460;scale=9;view=np.array([0,.35,-.93675]);view/=np.linalg.norm(view);right=np.array([-1,0,0]);up=np.cross(view,right);transform=np.array([right,up,view]);height=10;origin=np.array([0,10,0]);energy=np.zeros((H,W,3));stats=[];cache={}
    def texture(name):
        if name not in cache:cache[name]=np.asarray(Image.open(assets/name).convert('RGBA'),float)/255
        return cache[name]
    for name,data in buffers(assets/'iris_fx_muzzle_fire.mesh'):
        assert data.shape[1]==13;d=materials[name];p=data[::4];dt=time-p[:,6];life=p[:,7];t=np.clip(dt/life,0,1);alive=(dt>=0)&(dt<life);alpha=np.full(len(p),d['colors'][1][3]);ci,cm,co=np.asarray(d['colors']);fi=d['fade_in'];fo=d['fade_out'] if native_fade else 1-d['fade_out']
        alpha=np.where(t<fi,ci[3]+(cm[3]-ci[3])*np.clip(t/max(.001,fi),0,1),np.where(t>fo,cm[3]+(co[3]-cm[3])*np.clip((t-fo)/max(.001,1-fo),0,1),cm[3]))
        i0,i1,i2,i3=d['intervals'];f=np.clip((t-i0)/max(.001,i1-i0),0,1);g=np.clip((t-i2)/max(.001,i3-i2),0,1);color=np.where((t<i1)[:,None],ci*(1-f[:,None])+cm*f[:,None],np.where((t<i2)[:,None],cm,cm*(1-g[:,None])+co*g[:,None]));color[:,3]=alpha
        if native_fade:
            # 独立消费实际源四个区间；零宽端段应保持中间色，符合原引擎Update，不沿用旧错误公式。
            color[:,:3]=cm[:3]
            if i1!=i0:
                a=t<i1;color[a,:3]=ci[:3]*(1-f[a,None])+cm[:3]*f[a,None]
            if i3!=i2:
                a=(t>=i1 if i1!=i0 else np.ones(len(t),dtype=bool))&(t>i2);color[a,:3]=cm[:3]*(1-g[a,None])+co[:3]*g[a,None]
        size=np.interp(t,np.linspace(0,1,17),d['size_curve17']);r=p[:,8]*size;angle=p[:,9]+p[:,12]*np.maximum(dt,0);centers=p[:,:3]+p[:,3:6]*np.maximum(dt,0)[:,None]+.5*np.asarray(d['acceleration'])*np.maximum(dt,0)[:,None]**2+[0,height,0];centers=(centers-origin)@transform.T;centers[:,:2]=centers[:,:2]*[scale,-scale]+[W/2,H/2];before=energy.sum()
        for j in np.flatnonzero(alive&(r>.001)&(alpha>.00001)):
            rr=r[j]*scale*1.42;cx,cy=centers[j,:2];lo=np.maximum(0,np.floor([cx-rr,cy-rr]).astype(int));hi=np.minimum([W-1,H-1],np.ceil([cx+rr,cy+rr]).astype(int))
            if np.any(hi<lo):continue
            x,y=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);x=(x-cx)/scale/r[j];y=-(y-cy)/scale/r[j];cs,sn=math.cos(angle[j]),math.sin(angle[j]);u=(cs*x+sn*y+1)*.5;v=(-sn*x+cs*y+1)*.5;mask=(u>=0)&(u<=1)&(v>=0)&(v<=1);uv=np.stack((u,v),-1)
            cols,rows,count=d['atlas_grid'];frame=t[j]*(count-1);f0=math.floor(frame);f1=min(count-1,f0+1);image=texture(d['texture']);inset=np.array([.5/image.shape[1],.5/image.shape[0]])
            def tex(n):
                q=np.clip(uv/[cols,rows],inset,1/np.array([cols,rows])-inset)+np.array([n%cols,n//cols])/[cols,rows];return sample(image,q*np.asarray(d['uv'][2:])+d['uv'][:2])
            texel=tex(f0)*(1-(frame-f0))+tex(f1)*(frame-f0);rgb=sample(texture(d['palette']),np.stack((texel[...,1],np.full(u.shape,color[j,1]*d['base_color'][0])),-1),True)[...,:3] if d['grey_color'] else texel[...,:3]*color[j,:3]*d['base_color'][:3]
            alpha2=texel[...,3]*alpha[j]*d['base_color'][3]
            if d['grey_alpha']:alpha2=sample(texture(d['palette']),np.stack((texel[...,3],np.full(u.shape,alpha[j]*d['base_color'][3])),-1),True)[...,3]*alpha[j]*d['base_color'][3]
            mask&=alpha2>=.002;contribution=rgb*alpha2[...,None]*d['gain'];sl=(slice(lo[1],hi[1]+1),slice(lo[0],hi[0]+1));energy[sl][mask]+=contribution[mask]
        stats.append({'layer':name,'energy':float(energy.sum()-before)})
    return Image.fromarray((np.clip(energy+[.53,.36,.29],0,1)*255).astype('uint8')),stats

def main():
    out=ROOT/'docs/previews051';out.mkdir(exist_ok=True);doc=json.loads((ROOT/'docs/eight-effects.json').read_text('utf8'));materials=doc['materials'];rows=[];sheet=Image.new('RGB',(560*4,480*2))
    for row,native in enumerate((False,True)):
        for col,t in enumerate((.15,.4,.8,1.3)):
            im,stats=muzzle_frame(A,materials,t,native);ImageDraw.Draw(im).text((12,10),f'CPU actual mesh / {"native fade start" if native else "old fade duration"} / {t:.2f}s',fill='white');sheet.paste(im,(col*560,row*480));rows.append({'native_fade':native,'time':t,'layers':stats})
    buf=BytesIO();sheet.save(buf,format='JPEG',quality=93);put(out/'muzzle-before-after.jpg',buf.getvalue(),'源枪口CPU动态预览','实际52字节粒子/图集/LUT/17点尺寸/旋转与20触发，比较源fade开始百分比；非GPU')
    import preview_electro050 as ep,scene_geometry as geo
    area=Image.new('RGB',(2400,1000));result=[]
    # 旧例是已部署050的真实buffer/曲线快照；游戏更新后不能再从游戏目录读取“旧版”。
    import copy
    before=json.loads((ROOT/'docs/source-effects-051-before.json').read_text('utf8'));latest=geo.mesh(A/'iris_fx_electro_area.mesh');newdoc=copy.deepcopy(ep.doc);liveattrs=ep.attrs
    for row in range(2):
        ep.A=A;ep.doc=copy.deepcopy(newdoc);ep.parts=copy.deepcopy(latest);ep.states,ep.duration,ep.bound=curves(A/'effect_curves.csv','electro_area');ep.textures={};ep.attrs=liveattrs
        if row==0:
            saved={r['name']:np.asarray(r['values']) for r in before['electro_buffers']}
            ep.states=np.asarray(before['electro_curves'])
            for part in ep.parts:
                part['p']=saved[part['name']][:,:3].copy();mat=ep.doc['materials'][part['name']]
                if 'burst_card_center' in mat:mat['burst_card_center']=((part['p'].min(0)+part['p'].max(0))*.5).tolist()
            ep.attrs=lambda part:(saved[part['name']][:,3:6],saved[part['name']][:,6:10],saved[part['name']][:,10:12])
        for col,t in enumerate((.1,.25,.5,.8)):
            im,layers,stats=ep.frame(t,10);ImageDraw.Draw(im).text((12,12),f'CPU / {"051 source visible envelope" if row else "050 geometry envelope"} / {t:.2f}s',fill='white');area.paste(im,(col*600,row*500));result.append({'revision':51 if row else 50,'time':t,'layers':layers,**stats})
    buf=BytesIO();area.save(buf,format='JPEG',quality=93);put(out/'electro-before-after.jpg',buf.getvalue(),'源电脉实际像素预览','同一真实源mesh/LUT/曲线与固定高度10；仅整套源量尺变化，不重新拼造效果')
    record={'muzzle':rows,'electro':result,'compiled':False,'GPU_tested':False,'method':'actual serialized mesh + source textures/materials/curves; bright background; CPU rasterization'}
    put(out/'pixel-evidence.json',json.dumps(record,ensure_ascii=False,indent=2),'051像素证据','逐层实际贡献，不能用文件存在或源码关键词冒充可见性')
    print('PREVIEW051_OK',flush=True)
if __name__=='__main__':main()
