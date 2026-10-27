"""050离线坐锤：真实人体下臀表面落在实际锤体顶面，不强写游戏角色位置。"""
from functools import lru_cache
from pathlib import Path
import numpy as np
import port_math as m
import scene_geometry as geo
import seated_pose
from safeio import ROOT
GAME=Path('D:/steam/steamapps/common/Kenshi')

@lru_cache(maxsize=2)
def models(sex):
    body=geo.mesh(GAME/f'data/character/meshes/human/human_{sex}.mesh');weapon=geo.mesh(ROOT/'package/IrisArsenal/assets/iris_weapon.mesh')
    bones=m.skeleton(GAME/f'data/character/meshes/{sex}_skeleton/{sex}_skeleton.skeleton');ids={b['name']:b['id'] for b in bones}
    # 原生Pelvis主要蒙皮的最低10%是真实下臀接触样本；固定顶点身份，避免逐帧换点抖动。
    w=body[0]['weights'];vi=np.unique(w[(w[:,1]==ids['Bip01 Pelvis'])&(w[:,2]>.5),0].astype(int));p=body[0]['p'][vi];low=np.percentile(p[:,1],10);selection=vi[p[:,1]<=low]
    assert len(selection)>=8
    return body,weapon,bones,ids,selection

def posed(bones,frame):
    qs,dy,prop,offset=frame;pb=[dict(b) for b in bones];ids={b['name']:b['id'] for b in bones};local=[m.qmul(b['orientation'],q) for b,q in zip(bones,qs)]
    pb[0]['position']=m.vadd(pb[0]['position'],(0,dy,0));pb[ids['Bip01 Pelvis']]['position']=m.vadd(pb[ids['Bip01 Pelvis']]['position'],offset);pb[ids['Bip01 Prop2']]['position']=m.vadd(pb[ids['Bip01 Prop2']]['position'],prop)
    return pb,local,m.world(pb,local)

def support(weapon,grip,q,anchor):
    # 用主实体真实三角面向下投影。每个候选柱只取最高交点，避免选到锤底或侧壁；
    # 需要±0.20的接触小片均有支撑，不把装饰尖刺/边缘的一点触碰当成能坐。
    actual=m.qmul(q,m.axis((1,0,0),90));rot=geo.rotation(actual);part=weapon[0];p=part['p']@rot.T+grip;tri=p[part['tri']];a,b,c=tri[:,0],tri[:,1],tri[:,2]
    den=(b[:,2]-c[:,2])*(a[:,0]-c[:,0])+(c[:,0]-b[:,0])*(a[:,2]-c[:,2]);valid=abs(den)>1e-9;safe=np.where(valid,den,1)
    def height(x,z):
        u=((b[:,2]-c[:,2])*(x-c[:,0])+(c[:,0]-b[:,0])*(z-c[:,2]))/safe;v=((c[:,2]-a[:,2])*(x-c[:,0])+(a[:,0]-c[:,0])*(z-c[:,2]))/safe;hit=valid&(u>=0)&(v>=0)&(u+v<=1)
        return float(np.max((u*a[:,1]+v*b[:,1]+(1-u-v)*c[:,1])[hit])) if hit.any() else None
    candidates=[]
    for x in np.arange(anchor[0]-4,anchor[0]+4.001,.16):
        for z in np.arange(anchor[2]-4,anchor[2]+4.001,.16):
            ys=[height(x+dx,z+dz) for dx,dz in [(0,0),(-.2,0),(.2,0),(0,-.2),(0,.2)]]
            if any(y is None for y in ys) or max(ys)-min(ys)>.5:continue
            point=np.array([x,max(ys),z]);distance=np.linalg.norm(point-anchor)
            candidates.append((distance,point))
    assert candidates,'源坐姿附近没有实际主锤顶面，不能靠任意偏移假装接触'
    point=min(candidates,key=lambda x:x[0])[1];return (point-grip)@rot,point

def calibrate(bones,frames,spec,sex):
    body,weapon,bind,ids,selection=models(sex);times=np.linspace(0,spec['duration'],len(frames));reference=int(np.argmin(abs(times-2.0)))
    pb,local,wp=posed(bones,frames[reference]);skinned=geo.skin(body,bind,wp);anchor=skinned[0]['p'][selection].mean(0);grip,q=wp[ids['Bip01 Prop2']]
    seat_local,_=support(weapon,np.asarray(grip),q,anchor);output=[];audit=[]
    for t,frame in zip(times,frames):
        weight=m.smooth((t-1.5)/.25)*(1-m.smooth((t-2.75)/.35));pb,local,wp=posed(bones,frame);old_rh=np.asarray(wp[ids['Bip01 R Hand']][0]);old_lh=np.asarray(wp[ids['Bip01 L Hand']][0]);rq=wp[ids['Bip01 R Hand']][1];lq=wp[ids['Bip01 L Hand']][1]
        grip,q=wp[ids['Bip01 Prop2']];actual=m.qmul(q,m.axis((1,0,0),90));seat=np.asarray(grip)+geo.rotation(actual)@seat_local
        anchor=geo.skin(body,bind,wp)[0]['p'][selection].mean(0);delta=(seat+[0,.03,0]-anchor)*weight
        pelvis=ids['Bip01 Pelvis'];parent=pb[pelvis]['parent'];ld=m.rotate(m.qi(wp[parent][1]),delta);pb[pelvis]['position']=m.vadd(pb[pelvis]['position'],ld)
        wp=seated_pose.solve_arm(pb,local,'R',old_rh,rq);wp=seated_pose.solve_arm(pb,local,'L',old_lh,lq)
        new_qs=[m.qnorm(m.qmul(m.qi(b['orientation']),q)) for b,q in zip(bones,local)];total=m.vadd(frame[3],ld);output.append((new_qs,frame[1],frame[2],total))
        anchor_after=geo.skin(body,bind,wp)[0]['p'][selection].mean(0);error=float(np.linalg.norm(anchor_after-seat-[0,.03,0]));right=float(np.linalg.norm(np.asarray(wp[ids['Bip01 R Hand']][0])-old_rh));left=float(np.linalg.norm(np.asarray(wp[ids['Bip01 L Hand']][0])-old_lh))
        if weight>.999:audit.append({'time':float(t),'contact_error':error,'right_hand_error':right,'left_hand_error':left})
    assert max(x['right_hand_error'] for x in audit)<.001 and max(x['left_hand_error'] for x in audit)<.6,(spec['key'],sex,audit)
    spec.setdefault('seat050',{})[sex]={'basis':'native skinned lower-pelvis patch / actual solid hammer roof','support_local_held_mesh':seat_local.tolist(),'selection_vertices':selection.tolist(),'contact_error_max':max(x['contact_error'] for x in audit),'right_hand_error_max':max(x['right_hand_error'] for x in audit),'left_hand_error_max':max(x['left_hand_error'] for x in audit),'runtime_actor_write':False,'frames':audit}
    return output
