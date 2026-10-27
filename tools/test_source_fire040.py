# 047只增加电脉范围一资产/一曲线；原钻头/火焰断言保持，消费端计数同步。
"""040实源引用/空间相似变换/完整序列化/一次终结球与枪口生命周期；不替代实机观感。"""
import json,hashlib,re,math
from pathlib import Path
import numpy as np
from safeio import ROOT
from test_drill_visibility import buffers
from fire_burst import nodes,part_bounds

HASHES={'VoiceFlameWaveProject03.nif':'25c671a705f73ec939dfcf03ff0899358456386891a939906ff68968251f910b','MPSFireWaveFlames.nif':'3e3bb4fd95a0952c76f8e3e2c7d4bf6a4fbde85272a12a46a267d7e39178572d','MPSFireBoltImpact01.nif':'1bc018c4d9d9102803869624be504c8dcde645dff7dee6616b950644b054ae3e'}
def verify_source040():
    A=ROOT/'package/IrisArsenal/assets';fx=json.loads((ROOT/'docs/eight-effects.json').read_text('utf8'));fire=json.loads((ROOT/'docs/fire-burst-040.json').read_text('utf8'));muzzle=json.loads((ROOT/'docs/muzzle-fire-042.json').read_text('utf8'));burst=json.loads((ROOT/'docs/drill-burst-041.json').read_text('utf8'))
    for name,digest in HASHES.items():assert hashlib.sha256((ROOT/'tools/source-cache'/name).read_bytes()).hexdigest()==digest
    assert fire['addon_count']==7 and len(fire['layers'])==14 and len(fire['geometry']['shapes'])==6
    assert all(m['rank']==3 for m in fire['geometry']['shapes'])
    assert fire['chain'][1:4]==['Skyrim.esm:SPEL 0003F9ED','MGEF 000562EB','PROJ 000647BE']
    assert muzzle['chain'][-2:] == ['Skyrim.esm:ADDN 0002B95B','MPS/MPSFireBoltImpact01.nif']
    original_nodes=nodes(Path(fire['source']));serialized=list(buffers(A/'iris_fx_fire_blast.mesh'))
    assert len(serialized)==8 and len(list(buffers(A/'iris_fx_drill_blast.mesh')))==13
    import author_prototype as author
    original,_=author.read_nif(Path(fire['source']));original={m['name']:m for m in original}
    # 读回真正的网格字节对照原几何，允许的只有全体一个固定尺度和轴变换；拒绝各片随意摆放。
    for (mat,data),shape in zip(serialized[:6],fire['geometry']['shapes']):
        m=original[shape['name']];p=(np.asarray(m['vertices'])@m['matrix'][:3,:3].T+m['matrix'][:3,3])@author.C.T*author.SCALE/fire['source_peak']
        assert np.allclose(data[:,:3],p,atol=1e-6)
    for (name,data),layer in zip(serialized[6:],fire['render_layers']):
        assert name==layer['material'] and np.allclose(data[::4,:10],layer['particles'],atol=1e-6)
        assert len(layer['source_nodes'])==7
        material=fx['materials'][name];rotation=layer['source_rotation'];assert rotation['speed']==0 and rotation['variation']==0
        assert all(rotation['angle']-rotation['angle_variation']-1e-6<=q[9]<=rotation['angle']+rotation['angle_variation']+1e-6 for q in layer['particles'])
        assert material['texture'] and material['palette'] and material['acceleration'][1]>0
        assert material['atlas_grid'] in ([8,4,32],[2,2,4])
    for layer in fire['layers']:
        assert np.allclose(layer['source_world_matrix'],original_nodes[layer['addon_node']]['world'])
    # 七节点实际共享容量，不能把300/210误当每处一份；所有源.birth/live均满足原池上限。
    for name in set(l['material'] for l in fire['layers']):
        layers=[l for l in fire['layers'] if l['material']==name];changes=[]
        for layer in layers:
            for q in layer['particles']:changes.extend([(q[6],1),(q[6]+q[7],-1)])
        active=0;peak=0
        for time,delta in sorted(changes):active+=delta;peak=max(peak,active)
        assert peak<=layers[0]['source_capacity']
    assert len(muzzle['layers'])==5 and len(muzzle['trigger_times'])==20
    for (name,data),layer in zip(buffers(A/'iris_fx_muzzle_fire.mesh'),muzzle['layers']):
        assert name==layer['material'] and np.allclose(data[::4,:10],np.asarray(layer['particles'])[:,:10],atol=1e-5)
    assert burst['phase_timing']=={'blue_end':.52,'fire_begin':.56}
    # 蓝相和火相的出生时钟相隔0.56秒；两个资产共用同源材质/位置/尺寸，不再借通用FireballExp。
    for base,later in zip(fire['layers'],burst['fire']['layers']):
        a=np.array(base['particles']);b=np.array(later['particles']);scale=burst['fire']['coverage_calibration']['uniform_scale'];assert later['material']==base['material']+'/Coverage041/drill'
        assert np.allclose(a[:,[0,1,2,3,4,5,8]]*scale,b[:,[0,1,2,3,4,5,8]],atol=1e-7) and np.allclose(a[:,[7,9]],b[:,[7,9]]) and np.allclose(b[:,6]-a[:,6],.56)
    # 本轮没有生成替代贴图；全部新火焰像素都走现有BSA/原资源同像素核验链。
    used={fx['materials'][n][k] for n,_ in serialized for k in ('texture','palette','diffuse') if k in fx['materials'][n]}
    known={t['output'] for t in fx['textures']}|{'iris_white.dds'};assert used<=known
    moves=json.loads((ROOT/'docs/eight-moves.json').read_text('utf8'))['moves'];events=moves[4]['events']
    assert [(e['kind'],e['multiplier'],e['radius']) for e in events]==[('blade',2,4),('blade',2,4),('shockwave',3,90)]
    c=(ROOT/'IrisCombat.cpp').read_text('utf8');trace=c[c.index('bool TraceBladeWindows'):c.index('Vector3 WingCenter')]
    assert 'n<2' in trace and 'FULL_BURST_REACH' in trace and 'const float FULL_BURST_REACH=90.f' in c
    assert 'a.move==4?muzzle:c->getPosition()' in c and 'Path(p,p,radius,true)' in c and 'a.move!=4,a.move==4?c->getOrientation():Quaternion::IDENTITY' in c
    assert c.count('->_NV_hitByMeleeAttack(')==1 and c.count('KenshiLib::AddHook(')==3
    for token in ['a.muzzleFire.Clear(alive)','a.muzzleFire.Hide();','Borrow(a.muzzleFire,"muzzle_fire")','muzzleAge=a.move==5','moves[5].events.front().time','key=="muzzle_fire"']:assert token in c,token
    assert 'count!=20' in c and 'count!=14' in c
    material=(A/'iris_eight.material').read_text('utf8');shader=(A/'iris_eight.hlsl').read_text('utf8')
    assert 'sourceAcceleration*et*et' in shader and material.count('param_named sourceAcceleration float3')>=8
    # 原源明示的重力确实产生Y方向升腾；其余动态未知项在来源说明中列为未移植，不编造。
    first=fire['layers'][0];assert any(f['constant_applied'] and abs(f['strength']-58.499996)<.001 for f in first['source_forces'])
    bound=np.array(part_bounds(fire['layers']));mesh_radius=__import__('struct').unpack('<7f',(A/'iris_fx_fire_blast.mesh').read_bytes()[-28:])[-1]
    assert np.linalg.norm(bound,axis=1).max()<=mesh_radius+1e-5
    return {'reference_seconds':{'fire':[109.8,112.5],'muzzle':[92,94]},'source_hashes':HASHES,'source_geometry_shapes':6,'source_addons':7,'fire_submeshes':8,'drill_submeshes':13,'muzzle_layers':5,'source_layout_unchanged':True,'terminal_sphere':{'radius':90,'multiplier':3,'events':1,'old_third_blade_removed':True},'source_linear_gravity':True,'runtime_full_NiPSys':False,'compiled':False,'game_tested':False,'visual_match_verified':False}
if __name__=='__main__':print(json.dumps(verify_source040(),ensure_ascii=False,indent=2))
