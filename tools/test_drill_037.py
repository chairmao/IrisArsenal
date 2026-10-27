# 047只增加电脉范围一资产/一曲线；原钻头/火焰断言保持，消费端计数同步。
"""037真实源资产/序列化/消费链验证；不编译，不以离线模型冒充游戏效果。"""
from pathlib import Path
import hashlib,json,re,struct
import numpy as np
from safeio import ROOT
import verify_prototype as base

def verify_drill037():
    A=ROOT/'package/IrisArsenal/assets';effects=json.loads((ROOT/'docs/eight-effects.json').read_text('utf-8'));assets={x['key']:x for x in effects['assets']}
    assert len(assets)==20 and len(assets['drill_wings']['materials'])==10
    wing=assets['drill_wings'];assert Path(wing['source']).name=='EXDrill2.nif'
    assert {l['bone'] for l in wing['layers']}=={'AnimObjectA','AnimObjectB'}
    assert sum(l['vertices'] for l in wing['layers'])>100000
    assert hashlib.sha256(Path(wing['source']).read_bytes()).hexdigest()==wing['sha256']
    rows=(A/'effect_curves.csv').read_text('utf-8').split();assert rows[:3]==['IRIS_FX_CURVES','1','14'];at=3;streams={}
    for _ in range(14):
        key=rows[at];subs,n=int(rows[at+1]),int(rows[at+2]);duration,peak=float(rows[at+3]),float(rows[at+4]);at+=5
        states=np.asarray(list(map(float,rows[at:at+subs*n*25]))).reshape(subs,n,25);at+=subs*n*25;streams[key]=(states,duration,peak)
    assert at==len(rows)
    states,duration,peak=streams['drill_wings'];assert states.shape[0]==10
    assert np.max(np.ptp(states[:,:,13:],axis=1))>1
    # 实际流中每个翼形的矩阵必须保持刚体；不靠把轴缩成0再吹胀来伪造开合。
    rotations=states[:,:,13:].reshape(10,-1,3,4)[:,:,:,:3]
    assert np.allclose(np.linalg.det(rotations),1,atol=1e-5)
    assert np.allclose(np.matmul(rotations,np.swapaxes(rotations,-1,-2)),np.eye(3),atol=1e-5)
    from iris_wings import read_meshes,source_world
    import author_prototype as author
    from anim_skyrim import load_skyrim_animation,load_skyrim_skeleton
    specs=json.loads((ROOT/'docs/eight-moves.json').read_text('utf-8'))['moves'];spec=specs[3]
    assert [len(x['events']) for x in specs]==[2,3,4,12,3,20,3,4,4,3]
    cue={e['text']:e['time'] for e in spec['source_events']};begin=cue['PIE.$IrisEXDrill2']+.02;end=cue['PIE.$IrisEXDrillOFF']
    assert np.allclose([begin,end],wing['source_window']) and abs(duration-(end-begin))<1e-8
    clip=load_skyrim_animation(spec['sources'][0]);rig=load_skyrim_skeleton(str(author.SKEL));meshes=read_meshes(Path(wing['source']))
    vertices,mats=base.mesh(A/'iris_fx_drill_wings.mesh',48,True)
    H=np.eye(4);H[:3,:3]=author.C*author.SCALE;Hi=np.linalg.inv(H)
    # 从真正序列化的顶点+矩阵回到完整源HKX表达式，覆盖起手/出枪/合拢三段和A/B两侧全部10形状。
    sample_checks=[]
    for frame in (0,int((cue['PIE.$IrisEXDrillSHOOT']-begin)/duration*(states.shape[1]-1)),states.shape[1]-1):
        t=begin+duration*frame/(states.shape[1]-1);world=source_world(author,clip,rig,t);W=world[rig.bones.index('Weapon')]
        for i,(mesh,p) in enumerate(zip(meshes,vertices)):
            delta=states[i,frame,13:].reshape(3,4);actual=p@delta[:,:3].T+delta[:,3]
            source=np.asarray(mesh['vertices']);m=H@np.linalg.inv(W)@world[rig.bones.index(mesh['bone'])]@mesh['matrix']
            expected=source@m[:3,:3].T+m[:3,3];error=float(np.linalg.norm(actual-expected,axis=1).max())
            assert error<1e-4,(i,frame,error);sample_checks.append(error)
    burst=json.loads((ROOT/'docs/drill-burst-041.json').read_text('utf-8'))
    assert Path(burst['blue']['source']).name=='ALSEXP.nif' and Path(burst['fire']['source']).name=='VoiceFlameWaveProject03.nif'
    assert burst['phase_timing']['blue_end']<burst['phase_timing']['fire_begin']
    assert len(burst['fire']['layers'])==14 and len(burst['blue']['layers'])==1
    particles=0;extents=[]
    for group in ('blue','fire'):
        d=burst[group];assert hashlib.sha256(Path(d['source']).read_bytes()).hexdigest()==d['sha256']
        for layer in d['layers']:
            ps=layer['particles'];assert 0<len(ps)<=layer['source_capacity'];particles+=len(ps)
            assert layer['atlas'] in (1,2,4,8)
            for p in ps:
                assert len(p)==10 and p[7]>0 and p[8]>0
                if group=='blue':assert p[6]+p[7]<=burst['phase_timing']['blue_end']+1e-8
                else:assert p[6]>=burst['phase_timing']['fire_begin']
                for t in (0,p[7]):
                    q=np.array(p[:3])+np.array(p[3:6])*t;extent=p[8]*max(layer['size_curve'])*np.sqrt(2)
                    extents.extend([q-extent,q+extent])
    assert particles<1024
    fin=assets['drill_blast'];assert len(fin['materials'])==13
    assert all('explosionwarm0.nif' not in s['file'].lower() for s in fin['source_layers'])
    for name in fin['materials']:assert effects['materials'][name]['blend']!='one zero'
    # 钻天破终结的球R120、5倍、一次事件不因光学分层新增医疗。
    hits=spec['events'];assert sum(e['kind']=='heavy_shell' for e in hits)==1 and hits[-1]['radius']==120 and hits[-1]['multiplier']==5
    c=(ROOT/'IrisCombat.cpp').read_text('utf-8')
    for text in ('a.wings.Clear(alive)','a.wings.Hide();','a.wings.Draw(w,wingAge,1.f)','key=="drill_wings"','count!=20','count!=14','drill_finisher_ready'):
        assert text in c,text
    assert c.count('->_NV_hitByMeleeAttack(')==1 and c.count('KenshiLib::AddHook(')==3
    assert 'a.wings.Draw(w,wingAge,1.f)' in c and 'wingAge>=0?0:' in c
    shader=(A/'iris_eight.hlsl').read_text('utf-8');program=(A/'iris_eight.program').read_text('utf-8');materials=(A/'iris_eight.material').read_text('utf-8')
    for name in ('iris_burst_vp','iris_burst_fp'):assert name in shader and name in program
    # 源翼片镜面不降级到通用特效Lambert，也不污染原钻头/其他FX的共享材质。
    for mesh,name in zip(meshes,wing['materials']):
        d=effects['materials'][name];source=mesh['shader_data'];assert 'wing_metal' in d
        assert d['wing_metal']['strength']==source['specular_strength'] and d['wing_metal']['glossiness']==source['glossiness']
    assert 'iris_wing_metal_fp' in shader and 'shared_params_ref SharedSkyParams' in program and 'shared_params_ref AmbientParams' in program
    assert 'cameraPosition' in shader and 'inverseWorldView' in shader and 'sourceParticles' not in c
    # 源容量固定、每层一套共享材质；不按每帧/每粒创建Ogre实例或物理Actor。
    # 049新增原824火花一层；原终结层仍由本测试前面的源/逐顶点检查约束。
    assert materials.count('vertex_program_ref IrisBurstVP')==11 and materials.count('vertex_program_ref IrisMuzzleVP')==5 and materials.count('fragment_program_ref IrisBurstFP')==16
    return {'wings':{'source_shapes':10,'source_bones':['AnimObjectA','AnimObjectB'],'window':[begin,end],'serialized_source_error_max':max(sample_checks),'rigid_determinants':True},'burst':{'blue_geometry_layers':3,'blue_particle_layers':1,'fire_particle_layers':14,'finite_particles':particles,'phase_timing':burst['phase_timing'],'duration':burst['duration'],'source_particles_complete_runtime':False},'damage_contract':{'finisher_events':1,'radius':120,'multiplier':5},'compiler_run':False,'game_tested':False}

if __name__=='__main__':print(json.dumps(verify_drill037(),ensure_ascii=False,indent=2))
