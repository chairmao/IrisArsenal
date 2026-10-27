# 045：倍率与防御策略可配置，原几何/源素材回归仍保持；默认与完整开关组合由test_move_parameters045核验。
"""042十招真实产物回归：源事件、声明、纹理/曲线、物理消费；不代替GPU/游戏执行。"""
import json,re,hashlib
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from safeio import ROOT
from historical047 import original_specs047
from test_drill_visibility import buffers,curves
from fire_coverage import measure
from fire_burst import part_bounds

def verify_ten042():
    A=ROOT/'package/IrisArsenal/assets';doc=json.loads((ROOT/'docs/eight-moves.json').read_text('utf8'));moves=doc['moves']
    assert doc['contract']=='IRIS_EIGHT_042' and len(moves)==10
    cannon,combo=moves[8:];assert cannon['key']=='electro_cannon' and combo['key']=='hammer_combo'
    assert [(e['kind'],e['multiplier'],e['radius']) for e in cannon['events']]==[('front_sphere',1,25)]*4
    events=[e['time'] for e in cannon['source_events'] if e['text']=='PIE.$IrisBeam'];assert events==[e['time'] for e in cannon['events']]
    assert np.allclose(events,[1.8,2.05,2.3,2.6]) and cannon['attack_min']==0 and cannon['attack_max']==45
    assert all(e['kind']=='weapon' and e['multiplier']==1 for e in combo['events']) and len(combo['events'])==3
    assert np.allclose([e['time'] for e in combo['events']],[.33332,.633308,1.199958])
    assert len(combo['parts'])==2 and 'mco_powerattack1.hkx' in combo['parts'][0]['file'] and 'mco_attack9.hkx' in combo['parts'][1]['file']
    assert not any('Unarmed' in e['text'] for e in combo['source_events'])
    # 对照真正的改前规格，原八招全部时序/倍率/范围/根轨道/动画重定向输出保持。
    previous=None
    for p in sorted((ROOT/'docs/change-reports').glob('20261017-*.json')):
        if p.name<'20261017-184330':continue
        r=json.loads(p.read_text('utf8'))
        if Path(r['File'])==ROOT/'docs/eight-moves.json' and r['Safety']['backups']:
            previous=json.loads(Path(r['Safety']['backups'][0]).read_text('utf8'));break
    assert previous and previous['moves']==original_specs047(moves[:8],previous['moves'])
    c=(ROOT/'IrisCombat.cpp').read_text('utf8');main=(ROOT/'IrisArsenal.cpp').read_text('utf8');ranged=(ROOT/'IrisRanged.cpp').read_text('utf8')
    assert 'const unsigned MOVE_COUNT=10' in c and 'expected[MOVE_COUNT]={2,3,4,12,3,20,3,4,4,3}' in c
    branch=c[c.index('if(e.kind==9)'):c.index('if(e.kind==0||e.kind==3||e.kind==8)')]
    # 058修正缓存heading偏轴：原生枪口轴的前20/R25由共用几何及独立实际轨道回归验证。
    assert 'ElectroFrame(weapon,a.origin,c->getPosition(),e.radius,frame)' in branch and 'Path(center,center,e.radius,true)' in branch and branch.count('PushJob(j)')==1
    assert 'a.heading=c->getOrientation();' in c and 'a.cannon.Clear(alive)' in c and 'a.cannon.Hide();' in c
    assert 'if(a.move==9)return;' in c and 'if(a.move==9){a.trailPoints.clear();' in c
    assert 'DefaultBypass(unsigned move){return move==0||move==2||move==3||move==4||move==8;}' in c # 普通连击9不破格挡/闪避。
    assert c.count('->_NV_hitByMeleeAttack(')==1 and (main+c+ranged).count('KenshiLib::AddHook(')==18
    assert 'unsigned budget=64' in c and 'jobs.size()>=256' in c and '>=96' in c
    # 球是三维范围，不是地面圆。形体窄相位仍由既有PhysX完成；此处仅校验约定几何。
    for direction in ([0,0,1],[1,0,0],[.6,0,.8]):
        center=np.asarray(direction)*20
        for p,inside in [(center+[0,24.9,0],True),(center+[0,0,24.9],True),(center+[0,25.1,0],False)]:assert (np.linalg.norm(np.asarray(p)-center)<=25)==inside
    fx=json.loads((ROOT/'docs/eight-effects.json').read_text('utf8'));asset=next(x for x in fx['assets'] if x['key']=='electro_burst')
    assert Path(asset['source']).name=='beam.nif' and len(asset['materials'])==5
    assert not any('energy_kind' in fx['materials'][name] for name in asset['materials'])
    # 049横向统一824源坐标单位，逐顶点仍保持源五层及相对形状，不凭空添加环/准星。
    import author_effects as author
    from read_legacy_nif import read_legacy
    meshes,_=read_legacy(Path(asset['source']))
    for (_,p),mesh in zip(buffers(A/'iris_fx_electro_burst.mesh'),meshes):
        raw=(np.asarray(mesh['vertices'])@mesh['matrix'][:3,:3].T+mesh['matrix'][:3,3])@author.a.C.T*author.a.SCALE
        factor=fx['timelines']['electro_burst']['source_xy_scale049']
        assert np.allclose(p[:,:2],raw[:,:2]*factor,atol=1e-5)
    # 全力末击实际float32粒子/真实alpha轮廓覆盖原R90；未改蓝相/翻滚校准或伤害半径。
    full=json.loads((ROOT/'docs/fire-full-042.json').read_text('utf8'));cal=full['coverage_calibration'];layers=[]
    for (name,p),layer in zip(buffers(A/'iris_fx_full_blast.mesh')[-2:],full['render_layers']):
        assert name==layer['material'];v=p[::4,:10];assert np.allclose(v,layer['particles'],atol=1e-6);l=dict(layer);l['particles']=v.tolist();layers.append(l)
    ctx=SimpleNamespace(MATS=fx['materials'],TEXTURES={p.name:p.read_bytes() for p in A.iterdir() if p.suffix in ('.png','.dds')})
    obs=measure(ctx,[l for l in layers if l['name'].startswith('FlamesTall03')],np.linspace(.05,cal['source_body_window'][1],28));radius=np.asarray(obs['radius95_by_view'])*90
    assert min(radius)>90-1e-4 and moves[4]['events'][-1]['radius']==90 and moves[4]['events'][-1]['multiplier']==3
    assert 'move==4?"full_blast"' in c
    # 真实枪口52字节、17源尺寸/逐粒角速度，原5层/20触发/源贴图颜色保持。
    muzzle=json.loads((ROOT/'docs/muzzle-fire-042.json').read_text('utf8'));counts=[];spins=0
    for (name,p),layer in zip(buffers(A/'iris_fx_muzzle_fire.mesh'),muzzle['layers']):
        expected=np.asarray(layer['particles']);assert p.shape[1]==13 and np.allclose(p[::4,:10],expected[:,:10],atol=1e-5) and np.allclose(p[::4,12],expected[:,10],atol=1e-6)
        assert len(layer['size_curve17'])==17 and max(layer['size_curve17'])<=max(layer['size_curve'])+1e-5
        rotation=layer['source_rotation'];omega=expected[:,10]
        if rotation:
            spins+=1;assert np.all(abs(abs(omega)-rotation['speed'])<=rotation['variation']+1e-6)
        else:assert not np.any(omega)
        counts.append(len(expected))
    assert len(muzzle['layers'])==5 and len(muzzle['trigger_times'])==20 and spins==3 and counts==[393,240,79,120,78]
    mat=(A/'iris_eight.material').read_text('utf8');program=(A/'iris_eight.program').read_text('utf8');shader=(A/'iris_eight.hlsl').read_text('utf8')
    assert mat.count('vertex_program_ref IrisMuzzleVP')==5 and 'vertex_program IrisMuzzleVP hlsl' in program and 'VOut iris_muzzle_vp(MuzzleInput i' in shader and 'float curve[17]' in shader and 'i.uv.z*et' in shader
    for block in mat.split('vertex_program_ref IrisMuzzleVP {')[1:]:
        params=block.split('}',1)[0];assert 'sizeCurve ' not in params and 'sizeEnd ' not in params
        for name in ['sizeSamples0','sizeSamples1','sizeSamples2','sizeSamples3','sizeSampleEnd']:assert name in params
    return {'source_events':{'electro':events,'hammer':[e['time'] for e in combo['events']]},'electro_sphere':{'forward':20,'radius':25,'events':4,'multiplier_each':1,'collision':'existing native sphere queue'},'hammer':{'weapon_hits':3,'unarmed_events':0,'special_damage':False,'effects':False,'block_dodge':'native'},'full_blast':{'scale':cal['uniform_scale'],'world_radius95':radius.tolist(),'physical_radius':90},'muzzle':{'layers':5,'triggers':20,'stride':52,'size_samples':17,'rotating_source_layers':spins,'particles':counts,'Drag_turbulence':'not implemented'},'old_eight_specs_unchanged':True,'hooks':18,'compiled':False,'game_tested':False,'GPU_verified':False}

if __name__=='__main__':print(json.dumps(verify_ten042(),ensure_ascii=False,indent=2))
