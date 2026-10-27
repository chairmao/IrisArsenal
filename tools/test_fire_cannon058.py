"""058：实际原资产/原生持械轨道与视觉时钟、枪口轴的非编译验收。"""
import json,hashlib,math,re
import numpy as np
from safeio import ROOT
from historical047 import assert_047_hash
from test_melee_block043 import function
from test_drill_visibility import curves,buffers
import scene_geometry as g,port_math as m

def layer_age(key,index,t):
    if key in ('roll_blast','full_blast'):return t*2
    if key=='drill_blast' and index>=5 and t>.56:return .56+(t-.56)*2
    return t

def lifetime(key,t):
    if key in ('roll_blast','full_blast'):return t/2
    if key=='drill_blast':return .56+(t-.56)/2
    return t

def frame(muzzle,axis,root,radius=25):
    axis=np.asarray(axis,float);length=np.linalg.norm(axis)
    if not np.isfinite([*muzzle,*axis,*root,radius,length]).all() or length<.01 or radius<=0:return None
    axis=axis/length;center=muzzle+axis*(20-np.dot(muzzle-root,axis));reach=np.dot(center-muzzle,axis)+radius
    return (axis,center,reach) if np.isfinite(center).all() and math.isfinite(reach) and reach>0 else None

def verify_fire_cannon058():
    c=(ROOT/'IrisCombat.cpp').read_text('utf8');base=json.loads((ROOT/'docs/fire-cannon-058-baseline.json').read_text('utf8'));A=ROOT/'package/IrisArsenal/assets'
    # C++消费者必须同时向源采样和GPU粒子传同一层年龄；不能只改曲线让粒子仍慢放。
    for token in ['return age*2.f','layer>=5&&age>.56f','return .56f+(age-.56f)*2.f']:assert token in function(c,'VisualLayerAge')
    for token in ['return duration*.5f','return .56f+(duration-.56f)*.5f']:assert token in function(c,'VisualLifetime')
    draw=function(c,'Draw')
    for token in ['layerAge=VisualLayerAge(key,i,age)','layerAge/asset.duration','Ogre::Vector4(layerAge,opacity']:assert token in draw
    assert 'r.life=VisualLifetime(r.key,r.life)' in function(c,'Blast')
    assert 'r.age+=dt*r.rate' in function(c,'AdvanceEffects') and 'VisualLayerAge(r.key,5,r.age)' in function(c,'AdvanceEffects')
    timelines=[];checks=0
    for key,expected in [('roll_blast',8),('full_blast',8),('drill_blast',13)]:
        states,duration,_=curves(A/'effect_curves.csv',key);parts=buffers(A/f'iris_fx_{key}.mesh')
        assert len(parts)==states.shape[0]==expected
        begin=.56 if key=='drill_blast' else 0
        fire_start=5 if key=='drill_blast' else 0
        for source_t in np.linspace(begin,duration,97):
            actual_t=begin+(source_t-begin)/2
            for index in range(fire_start,len(parts)):
                assert abs(layer_age(key,index,actual_t)-source_t)<1e-12
                # 读取实际25维源曲线：加速后到达完全相同的源状态，不改变颜色、UV、膨胀或位置。
                def sample(t):
                    k=np.clip(t/duration*(states.shape[1]-1),0,states.shape[1]-1);lo=int(k);hi=min(states.shape[1]-1,lo+1)
                    return states[index,lo]*(1-(k-lo))+states[index,hi]*(k-lo)
                np.testing.assert_allclose(sample(layer_age(key,index,actual_t)),sample(source_t),atol=1e-6)
                checks+=1
        if key=='drill_blast':
            # 原资料确认蓝相0~.52，火相从.56开始；蓝5层每个时间点均保持原年龄。
            evidence=json.loads((ROOT/'docs/drill-burst-041.json').read_text('utf8'))
            assert evidence['blue']['phase_end']==.52 and evidence['blue']['life']<.56
            for index in range(5):
                for t in np.linspace(0,.56,113):assert layer_age(key,index,t)==t
            assert len(parts[-2][1])>0 and len(parts[-1][1])>0
        assert abs(layer_age(key,fire_start,lifetime(key,duration))-duration)<1e-8
        # dt仍用游戏时钟：暂停、半速、2倍速与原攻速独立；不改全局delta或演员rate。
        for game_speed in (0,.5,1,2,3):
            for attack_rate in (.6,1,1.8):
                dt=.01*game_speed*attack_rate
                if game_speed==0:assert layer_age(key,fire_start,begin+dt)==begin
                else:assert abs(layer_age(key,fire_start,begin+dt)-begin-2*dt)<1e-10
        timelines.append({'key':key,'source_duration':duration,'visual_game_duration_before_attack_rate':lifetime(key,duration),'fire_layers':expected-fire_start,'blue_layers_preserved':fire_start})
    for key in ('shock','blast','pulse_blast','beam','electro_area','muzzle_fire','fire_blast'):
        for t in (0,.2,.8,3,7):assert layer_age(key,0,t)==t and lifetime(key,t)==t

    # 实际序列化男女持械轨道，不只验证人工理想轴。
    spec=next(x for x in json.loads((ROOT/'docs/eight-moves.json').read_text('utf8'))['moves'] if x['key']=='electro_cannon');poses_report=[]
    for sex in ('male','female'):
        ids,poses,_=g.actual_frames(A/f'iris_action_electro_cannon_{sex}.skeleton',spec)
        for event in spec['events']:
            pose=poses[round(event['time']/spec['duration']*(spec['frames']-1))];grip,q=pose[ids['Bip01 Prop2']];q=m.qmul(q,m.axis((1,0,0),-90));rot=g.rotation(q)
            muzzle=np.asarray(grip)+rot@np.array([1.807138657,0,8.534358047]);root=np.array(pose[ids['Bip01']][0]);result=frame(muzzle,rot[:,2],root);assert result is not None
            axis,center,reach=result
            assert np.linalg.norm(np.cross(center-muzzle,axis))<1e-9
            assert abs(np.dot(center-root,axis)-20)<1e-9 and abs(reach-(np.dot(center-muzzle,axis)+25))<1e-9
            assert np.dot(axis,[0,0,1])>.98,(sex,event['time'],axis)
            poses_report.append({'sex':sex,'time':event['time'],'actual_muzzle':muzzle.tolist(),'axis':axis.tolist(),'sphere_center':center.tolist(),'reach':float(reach)})
    rng=np.random.default_rng(58019)
    for _ in range(2000):
        root=rng.uniform(-1e6,1e6,3);muzzle=root+rng.uniform(-15,15,3);axis=rng.normal(size=3);r=frame(muzzle,axis,root)
        assert r is not None;axis,center,reach=r
        assert np.linalg.norm(np.cross(center-muzzle,axis))<1e-8
        assert abs(np.dot(center-root,axis)-20)<1e-8
        # 浮动原点只影响渲染平移，不能改变方向或伤害球心。
        offset=rng.uniform(-1e5,1e5,3);b=frame(muzzle-offset,axis,root-offset)
        np.testing.assert_allclose(b[1]+offset,center,atol=1e-8,rtol=0)
    # 截图故障的负例：原生已转60度，旧起手heading仍朝Z，旧光柱不能共线。
    direction=np.array([math.sin(math.pi/3),0,math.cos(math.pi/3)])
    assert np.linalg.norm(np.cross(direction,[0,0,1]))>.8
    assert frame(np.zeros(3),np.zeros(3),np.zeros(3)) is None
    assert frame(np.zeros(3),[float('nan'),0,1],np.zeros(3)) is None
    assert frame(np.zeros(3),[0,0,1],np.zeros(3),0) is None
    electro=function(c,'ElectroFrame');emit=function(c,'Emit');show=function(c,'ShowParts')
    for token in ['weapon[0][2]','weapon[1][2]','weapon[2][2]','20.f-(frame.muzzle-root).dotProduct(frame.axis)','Vector3::UNIT_Z.getRotationTo(frame.axis)']:assert token in electro
    block=emit[emit.index('if(e.kind==9)'):emit.index('if(e.kind==0||e.kind==3||e.kind==8)')]
    cannon=show[show.index('float cannonAge='):show.index('// 原PROJ.NAM1')]
    assert 'ElectroFrame(weapon,a.origin,c->getPosition(),e.radius,frame)' in block and 'frame.orientation' in block
    assert 'ElectroFrame(w,a.origin,c->getPosition(),moves[8].events.front().radius,frame)' in cannon and 'Pose(frame.muzzle-a.origin,frame.orientation,Vector3(1,1,frame.reach))' in cannon
    assert 'a.heading' not in block+cannon and block.count('PushJob(j)')==1
    assert 'shotLogs[8]<20' in block
    for token in ('setOrientation(', 'setPosition(', 'lookatTarget(', 'Target(', 'AddHook(', 'CreateThread(', 'EnterCriticalSection('):assert token not in electro+block+cannon,token
    # 原安全窗口、医疗、角色反应/选招全部逐函数保持；不增加线程/Hook/PhysX调用。
    protected=['Flush','DamageTarget','Contacts','ResolveJobs','TryCapsuleBatch','Tick','Enemy','IgnoreRangedContact']
    for name in protected:assert hashlib.sha256(function(c,name).encode()).hexdigest()==base['functions']['IrisCombat.cpp'][name],name
    files=0
    for rel,digest in base['runtime'].items():
        if rel in ('IrisPackage.json','IrisArsenal.dll'):continue
        assert_047_hash('package:'+rel,hashlib.sha256((ROOT/'package/IrisArsenal'/rel).read_bytes()).hexdigest(),digest);files+=1
    from stage_package import BUILD_CONTRACT,validate_dll
    assert BUILD_CONTRACT=='IRIS_DRIVE_REBUILD_059' and 'IRIS_DRIVE_REBUILD_059' in c
    dll=ROOT.parent/'bin/Release/IrisArsenal.dll'
    if BUILD_CONTRACT.encode() not in dll.read_bytes():
        try:validate_dll()
        except RuntimeError as e:assert '059' in str(e)
        else:raise AssertionError('旧DLL冒充058')
    return {'code_contract':BUILD_CONTRACT,'timelines':timelines,'actual_curve_comparisons':checks,'actual_pose_samples':poses_report,'random_axis_origin_cases':2000,'preserved_runtime_files':files,'protected_combat_functions':protected,'source_assets_reused':True,'new_hooks':0,'new_threads':0,'compiled':False,'C++_executed':False,'GPU_tested':False,'game_tested':False}

if __name__=='__main__':print(json.dumps(verify_fire_cannon058(),ensure_ascii=False,indent=2))
