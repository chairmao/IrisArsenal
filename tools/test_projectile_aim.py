"""0.2.2投射物回归：大世界坐标反例、源等离子可视及按招式预热；不编译或运行游戏。"""
from pathlib import Path
import json,re,math
import numpy as np
from PIL import Image
from safeio import ROOT
A=ROOT/'package/IrisArsenal/assets'

def verify_aim():
    combat=(ROOT/'IrisCombat.cpp').read_text('utf-8')
    target=combat[combat.index('Vector3 Target('):combat.index('// 弹体自出生')]
    # 检查真正原生返回值的消费表达式，零原点场景无法揭露旧版重复偏移，必须用非零世界坐标。
    expression=re.search(r'Vector3 point=(target->getBoneWorldPosition\(bones\[i\]\)[^;]*);',target).group(1)
    assert expression=='target->getBoneWorldPosition(bones[i])'
    assert '_getDerivedPositionUpdated' not in target and '+offset' not in target
    cases=[]
    for origin in [np.array([0.,0.,0.]),np.array([-16300.,200.,29300.]),np.array([900000.,-50.,-700000.])]:
        shooter=origin+np.array([0.,12.,0.]);native_bone=origin+np.array([35.,13.,80.])
        # 原生骨点已在世界系；渲染枪口局部值只在另一个入口加一次origin。
        actual=native_bone.copy();direction=actual-shooter;direction/=np.linalg.norm(direction)
        assert np.allclose(direction,np.array([35.,1.,80.])/math.sqrt(35**2+1+80**2))
        assert np.linalg.norm(actual-shooter)<100
        if np.linalg.norm(origin)>1:assert np.linalg.norm(native_bone+origin-shooter)>10000
        scene_point=actual-origin;assert np.allclose(scene_point,[35.,13.,80.])
        cases.append({'origin':origin.tolist(),'world_aim':actual.tolist(),'distance':float(np.linalg.norm(actual-shooter))})
    assert 'Vector3 muzzle=Muzzle(weapon)+a.origin;' in combat
    assert 'shot.pos-origin-q*(asset.center*k)' in combat
    assert 's.target=e.kind==1?a.ground' not in combat # 地面弹仍走显式分支，不能覆盖其他招式。
    assert 's.target=a.ground;aim.source="intentional_ground_snapshot"' in combat
    for token in ['target_root=','raw_bone=','aim_source=','aim_distance=','shotLogs[s.move]<20','impactLogs[s.move]<20']:
        assert token in combat
    # 脉冲三发对应源ESP PlasmaBall，源三层和转换大小保持；R4.5核心、R36爆炸与装饰环区分。
    fx=json.loads((ROOT/'docs/eight-effects.json').read_text('utf-8'));shell=next(x for x in fx['assets'] if x['key']=='shell')
    assert Path(shell['source']).name=='PlasmaBall.nif' and len(shell['materials'])==3
    assert 27<shell['bound_radius']<28 and 's.visualRadius=e.kind==7?assets[s.visual.key].bound:s.collisionRadius;' in combat
    pulse=json.loads((ROOT/'docs/eight-moves.json').read_text('utf-8'))['moves'][6]
    assert len(pulse['events'])==3 and all(x['radius']==36 and x['multiplier']==2 for x in pulse['events'])
    assert 'float k=shot.visualRadius/asset.bound;' in combat
    # 预热必须由已启用权重决定。验证每个事件消费的真正资源，不为关闭招式加载钻头/光刃/光束。
    warm=combat[combat.index('void WarmNext()'):combat.index('bool Same(')]
    assert 'AssetRequired(i->first)&&!warmed.count(i->first)' in warm
    assert 'moves[i].weight>0' in combat[combat.index('bool AssetRequired('):combat.index('void WarmNext()')]
    active={'gun','blade','bullet','shell','blast','exhaust','muzzle','ion','pulse_blast','beam','shock','heavy','drill','drill_blast','fire_blast','charge_halo','drill_wings'}
    mats={name for x in fx['assets'] if x['key'] in active for name in x['materials']}
    # 粒子只有源烟尘贴图，没有普通网格的调色图；共享纹理预算要计入其真实资源。
    def textures(d):
        # 059专用光流/源准星没有通用palette槽，按实际Shader纹理绑定核对。
        if d.get('drive059_stream'):return [d['diffuse'],d['texture']]
        if d.get('drive059_surface'):return [d['diffuse']]
        return [] if (d.get('reference_reticle') or 'energy_kind' in d) else [d['texture'],d['palette']] if d.get('burst_particle') else [d['texture']] if d.get('particle') else [d['diffuse'],d['palette']]
    used={tex for name in mats for tex in textures(fx['materials'][name])}
    assert 'iris_fx_179f128b96e16ff2.png' not in (A/'iris_eight.material').read_text('utf-8')
    # 空包重建不会再产生已去重的历史PNG；直接对原DDS核对RGBA，避免拿旧产物作输入。
    shared=A/'iris_anim_rgba_179f128b96e16ff2.png'
    source=Path('E:/skyrimspecialedition/mods/soulworker_Iris/Textures/Soulworker/Iris/anim.dds')
    assert np.array_equal(np.array(Image.open(shared).convert('RGBA')),np.array(Image.open(source).convert('RGBA')))
    assert Image.open(shared).size==(2048,2048)
    def bytes_rgba_mips(name):
        w,h=Image.open(A/name).size;total=0
        while True:
            total+=w*h*4
            if w==h==1:return total
            w,h=max(1,w//2),max(1,h//2)
    new=sum(bytes_rgba_mips(x) for x in used if x.endswith('.png'))
    alltex={tex for x in fx['materials'].values() for tex in textures(x) if tex.endswith('.png')}
    old_bytes=sum(bytes_rgba_mips(x) for x in alltex)+bytes_rgba_mips(shared.name)
    # 此处只是RGBA8完整mip链估算，绝不等同DXGI/驱动实测总显存或泄漏结论。
    return {'world_coordinate_cases':cases,'native_world_point_used_unchanged':True,'pulse_source_layers':3,
            'pulse_visual_radius':shell['bound_radius'],'pulse_collision_radius':4.5,'pulse_blast_radius':36,
            'warm_keys':sorted(active),'available_assets':17,'texture_RGBA8_mips_estimate':{'old_eager_plus_duplicate_bytes':old_bytes,'enabled_and_shared_bytes':new,'reduction_bytes':old_bytes-new,'GPU_measured':False,'scope':'仅eight-effects材质纹理的RGBA8估计；钻头独立纹理与驱动实际分配未计入，不能用作总显存结论'},
            'compiled':False,'game_verified':False}
if __name__=='__main__':print(json.dumps(verify_aim(),ensure_ascii=False,indent=2))
