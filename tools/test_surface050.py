# 054仅更新当前交付版本/组包合同断言，原伤害、配置和资源回归条件保持。
"""050真实蒙皮/真实实体顶面、地下遮挡负例与版本门；不编译。"""
import json,hashlib
from pathlib import Path
import numpy as np
from safeio import ROOT
import scene_geometry as g,port_math as m

def surface_contact(spec,sex,ids,world,bones,indices=None):
    # 独立读取原生身体，按实际骨权找下臀；不拿作者自报的contact_error作为测试结果。
    game=Path('D:/steam/steamapps/common/Kenshi');body=g.mesh(game/f'data/character/meshes/human/human_{sex}.mesh');weapon=g.mesh(ROOT/'package/IrisArsenal/assets/iris_weapon.mesh')
    weights=body[0]['weights'];vi=np.unique(weights[(weights[:,1]==ids['Bip01 Pelvis'])&(weights[:,2]>.5),0].astype(int));selection=vi[body[0]['p'][vi,1]<=np.percentile(body[0]['p'][vi,1],10)]
    times=np.linspace(0,spec['duration'],spec['frames']);gaps=[];errors=[];hands=[]
    for k in (indices if indices is not None else np.flatnonzero((times>=1.8)&(times<=2.6))):
        posed=g.skin(body,bones,world[k]);anchor=posed[0]['p'][selection].mean(0);part=g.world_weapon(weapon,world[k],ids)[0];tri=part['p'][part['tri']];a,b,c=tri[:,0],tri[:,1],tri[:,2]
        den=(b[:,2]-c[:,2])*(a[:,0]-c[:,0])+(c[:,0]-b[:,0])*(a[:,2]-c[:,2]);good=abs(den)>1e-9;den=np.where(good,den,1);x,z=anchor[[0,2]]
        u=((b[:,2]-c[:,2])*(x-c[:,0])+(c[:,0]-b[:,0])*(z-c[:,2]))/den;v=((c[:,2]-a[:,2])*(x-c[:,0])+(a[:,0]-c[:,0])*(z-c[:,2]))/den;hit=good&(u>=0)&(v>=0)&(u+v<=1)
        assert hit.any(),(spec['key'],sex,times[k],'真实下臀下面没有锤体')
        roof=(u*a[:,1]+v*b[:,1]+(1-u-v)*c[:,1])[hit].max();gap=float(anchor[1]-roof);assert -.08<gap<.5,(spec['key'],sex,times[k],gap)
        gaps.append(gap);errors.append(abs(gap-.03))
    return {'seat_gap_min':min(gaps),'seat_gap_max':max(gaps),'samples':len(gaps),'contact_error_frames':errors}

def verify_surface050():
    A=ROOT/'package/IrisArsenal/assets';moves=json.loads((ROOT/'docs/eight-moves.json').read_text('utf8'))['moves'];results=[]
    # 059用户纠正drive应站立肩持；仅electro保留源PA6坐姿，drive由test_drive059验收。
    for i in (8,):
        for sex in ('male','female'):
            spec=moves[i];ids,world,bones=g.actual_frames(A/f"iris_action_{spec['key']}_{sex}.skeleton",spec);r=surface_contact(spec,sex,ids,world,bones);r.pop('contact_error_frames');results.append({'move':spec['key'],'sex':sex,**r})
    # 负例从已部署049真实骨架解出；必须检出腰靠/悬空，不能只对着新期望自证。
    fixture=json.loads((ROOT/'docs/seat-negative-049.json').read_text('utf8'));k=fixture['frame_index'];caught=False
    try:surface_contact(fixture['spec'],'female',fixture['ids'],{k:fixture['world_pose']},fixture['bones'],indices=[k])
    except AssertionError:caught=True
    assert caught,'旧049错误坐姿没有被真实表面测试检出'
    # 球心必须共用真实枪口高度。保留前20/R25；趴地且位于球心正下方的敌人仍在三维球内。
    spec=moves[8];ids,poses,_=g.actual_frames(A/'iris_action_electro_cannon_female.skeleton',spec);ys=[]
    for event in spec['events']:
        pose=poses[round(event['time']/spec['duration']*(spec['frames']-1))];grip,q=pose[ids['Bip01 Prop2']];q=m.qmul(q,m.axis((1,0,0),-90));y=float((np.asarray(grip)+g.rotation(q)@np.array([1.807138657,0,8.534358047]))[1]);ys.append(y)
        assert 0<y<25 and np.linalg.norm(np.array([0,0,20])-np.array([0,y,20]))<25
    cpp=(ROOT/'IrisCombat.cpp').read_text('utf8');emit=cpp[cpp.index('if(e.kind==9)'):cpp.index('if(e.kind==0||e.kind==3||e.kind==8)')]
    for token in ['ElectroFrame(weapon,a.origin,c->getPosition(),e.radius,frame)','r.pos=center','Path(center,center,e.radius,true)']:assert token in emit
    assert emit.count('PushJob(j)')==1 and cpp.count('->_NV_hitByMeleeAttack(')==1
    from stage_package import validate_dll,BUILD_CONTRACT
    assert BUILD_CONTRACT=='IRIS_DRIVE_REBUILD_059'
    dll=ROOT.parent/'bin/Release/IrisArsenal.dll'
    if BUILD_CONTRACT.encode() not in dll.read_bytes():
        try:validate_dll();raise AssertionError('旧DLL竟可通过050组包门')
        except RuntimeError:pass
    # 像素证据来自已实际执行的CPU光栅化；全部输入和输出摘要必须仍匹配，不能沿用过期预览。
    evidence=json.loads((ROOT/'docs/pixel-050-evidence.json').read_text('utf8'))
    # 051允许已经独立验收的精确源效果量尺迁移；050旧像素图仍仅证明050高度修复，不冒称当前画面。
    from historical047 import assert_047_hash
    for rel,digest in evidence['inputs'].items():
        actual=hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
        if rel.startswith('package/IrisArsenal/'):assert_047_hash('package:'+rel[len('package/IrisArsenal/'):],actual,digest)
        else:assert_047_hash('root:'+rel,actual,digest)
    assert hashlib.sha256((ROOT/'docs/previews050/electro-depth-before-after.jpg').read_bytes()).hexdigest()==evidence['image_sha256']
    assert evidence['GPU_tested'] is False and evidence['textures_changed'] is False
    for row in evidence['rows']:assert row['new_visible_pixels']>row['old_visible_pixels']*1.5 and row['additive_energy_ratio']>2
    return {'actual_skin_hammer_roof':results,'actual_muzzle_heights':ys,'prone_below_sphere_center':True,'same_visual_physical_center':True,'r25_forward20':True,'negative049_detected':caught,'compiled':False,'GPU_tested':False}
if __name__=='__main__':print(json.dumps(verify_surface050(),ensure_ascii=False,indent=2))
