"""034五招/真实圆柱/源地震与AOE静态验收；不编译、不把分析模型冒称原生运行。"""
from pathlib import Path
import json,math,re,struct,configparser,hashlib
import numpy as np
from PIL import Image
from safeio import ROOT
import verify_prototype as base

def verify_cannon_quake():
    A=ROOT/'package/IrisArsenal/assets';C=(ROOT/'IrisCombat.cpp').read_text('utf-8');N=(ROOT/'native/NativeMultiContact.cpp').read_text('utf-8');H=(ROOT/'native/FiniteCylinder.h').read_text('utf-8')
    # 独立解析标准：平端柱面之外的球/角落反例，胶囊端点外9单位不能当作柱体延长。
    def sphere(p,r):
        radial=max(0,math.hypot(p[0],p[1])-9);axial=max(0,-p[2],p[2]-10000)
        return radial*radial+axial*axial<=r*r
    cases=[([8.9,0,180],0,True),([9.1,0,180],0,False),([0,0,10001],.5,False),([0,0,10000.4],.5,True),([9.4,0,10000.4],.5,False),([9.3,0,10000.3],.5,True),([0,0,-1],.5,False),([0,0,359],0,True)]
    for p,r,hit in cases:assert sphere(p,r)==hit
    assert 'cylinder.Support(d)-body.Support(-d)' in H and 'body.points.size()==1' in H and 'return UNRESOLVED' in H and 'i<64' in H
    assert 'overlapOBBShapes(box,NX_ALL_SHAPES,64,batch,&collector,groups,0,true)' in N
    assert 'NxCreatePhysicsSDK' not in re.sub(r'//[^\n]*','',N) and 'setUserContactReport(' not in N
    for shape in ['NxSphereShape','NxCapsuleShape','NxBoxShape','NxConvexShape']:assert shape in N
    sdk=ROOT/'native/physx284/SDKs/Physics/include'
    methods={'NxSphereShape.h':'getWorldSphere','NxCapsuleShape.h':'getWorldCapsule','NxBoxShape.h':'getWorldOBB','NxConvexShape.h':'getConvexMesh','NxConvexMesh.h':'getBase','NxScene.h':'overlapOBBShapes'}
    for f,method in methods.items():assert method in (sdk/f).read_text('utf-8-sig')
    assert 'muzzle+d*reach,e.radius,false,true' in C and 'Vector3(r.radius,r.radius,r.length)' in C
    assert 'if(r.length<=.0001f){r.visual.Hide();return;}' in C and 'if(path.cylinder)' in C and 'r.length=length' in C
    # 真实序列化光管及每个源控制器采样的空间包络必须是同一单位柱体，不能只改碰撞。
    fx=json.loads((ROOT/'docs/eight-effects.json').read_text('utf-8'));beam=fx['timelines']['beam'];norm=beam['cylinder_normalization'];assert norm['target_radius']==1 and norm['target_z']==[0,1]
    raw=(A/'effect_curves.csv').read_text('utf-8').split();at=3;radial=0;lo=1e9;hi=-1e9
    for _ in range(int(raw[2])):
        key=raw[at];subs,n=int(raw[at+1]),int(raw[at+2]);at+=5;v=np.array(list(map(float,raw[at:at+subs*n*25]))).reshape(subs,n,25);at+=subs*n*25
        if key!='beam':continue
        points,_=base.mesh(A/'iris_fx_beam.mesh',48,True);assert len(points)==3
        for p,track in zip(points,v):
            for state in track:
                m=state[13:].reshape(3,4);q=p@m[:,:3].T+m[:,3];radial=max(radial,float(np.linalg.norm(q[:,:2],axis=1).max()));lo=min(lo,float(q[:,2].min()));hi=max(hi,float(q[:,2].max()))
    assert .99<radial<=1.0001 and -.0001<=lo<.001 and .999<hi<=1.0001
    # 用户改用215～217秒火焰版：真实六层火焰源几何/时间流，四次健康事件不增加。
    quake=fx['quake'];assert quake['style']=='fire' and quake['reference_seconds']==[215,217] and quake['layers']==6
    shock=next(x for x in fx['assets'] if x['key']=='shock');assert Path(shock['source']).name=='explosionwarm0.nif' and len(shock['materials'])==6
    assert fx['timelines']['shock']['duration']==4 and 'quake_profile.csv' not in C
    assert 'r.pos-origin+Vector3(0,r.key=="shock"?.8f:0.f,0)' in C and 'r.life=(shock||move==0||move==3||move==4||move==6)?assets[r.key].duration' in C
    # 准星只有平面轮廓，源录像重建身份明确，不把任意球形NIF当作找到的准星。
    marker=next(x for x in fx['assets'] if x['key']=='muzzle');assert marker['reference_reconstruction'] and len(marker['materials'])==2
    points,mats=base.mesh(A/'iris_fx_muzzle.mesh',48);q=np.concatenate(points)
    assert abs(q[:,2]).max()<1e-8 and np.ptp(q[:,0])>2 and np.ptp(q[:,1])>2
    assert 'Vector3::UNIT_Z.getRotationTo(axis)' in C and 'Pose(Muzzle(w)+axis*.8f,reticle' in C
    shader=(A/'iris_eight.hlsl').read_text('utf-8');material=(A/'iris_eight.material').read_text('utf-8');program=(A/'iris_eight.program').read_text('utf-8')
    assert 'iris_reticle_fp' in shader and 'IrisReticleFP' in program and 'IrisQuakeVP' not in program
    for name in marker['materials']:
        d=fx['materials'][name];assert d['reference_reticle']
        block=material.split('material '+name+'\n',1)[1].split('\nmaterial ',1)[0];assert 'IrisReticleFP' in block
    pulse=next(x for x in fx['assets'] if x['key']=='pulse_blast')
    for name in pulse['materials']:assert fx['materials'][name]['presentation']==[2.2,1.45]
    assert 'alpha=saturate(alpha*presentation.x)*clock.y;rgb*=presentation.y;' in shader
    # 射程放大不等于多存沿途全部世界shape：流式最近阻挡与完整列表min在乱序/重复/稠密输入下等价。
    rng=np.random.default_rng(33)
    for count in [0,1,64,257,4096]:
        contacts=[(float(rng.random()),bool(rng.integers(0,2))) for _ in range(count)]
        expected=min((t for t,char in contacts if not char),default=1)
        for _ in range(3):
            rng.shuffle(contacts);best=1
            for t,char in contacts:
                if not char:best=min(best,t)
            assert best==expected
    assert 'class TerrainRayCollector' in N and 'RayBlocker(world,from,motion,groups,obstruction,queryCalls)' in N
    ranged=(ROOT/'IrisRanged.cpp').read_text('utf-8')
    assert 'd->idata["range"]=int(ceilf(range));' in ranged and 'd->idata["range"]=360' not in ranged
    for token in ['ranged_gate actor=','outside_FCS_range','waiting_native_shot_gate','plugin_ready=','gateLogs++<32']:assert token in ranged
    # 优化只合并相同完整查询事实，保留每个Job独立受害名单/健康事件；不跨帧存物理指针。
    query=C[C.index('bool Contacts(GameWorld*'):C.index('void Collect(')]
    assert query.index('queuesAreClearMT()')<query.index('sphereFacts.size()') and query.index('budget<required')<query.index('IrisNative::OverlapSphere')
    assert '(path.cylinder||terrain)?2U:1U' in query and 'budget-=std::min(budget,calls)' in query and 'sphereFacts.size()<16' in query
    assert 'sphereFacts.clear(); // 只复用本安全帧' in C and 'QueryMetrics' not in C and '++epoch;sphereFacts.clear()' in C
    assert 'std::set<hand> victims' in C and 'r.event=j.event' in C and 'hurts.push_back(r)' in C
    # 053保留64查询预算，医疗改为独立可配软预算；原1ms字面值不再是现行合同。
    assert 'unsigned budget=64' in C and 'while(queueSnapshot.done<damageFlushMaxHits' in C and '>=damageFlushBudgetMs' in C
    assert 'IrisDiagnostics::QUERY_CACHE' in C and 'FPS_measured=0' in (C+(ROOT/'IrisDiagnostics.cpp').read_text('utf8')) and 'if(queryNotices<16)' in C
    ini=configparser.ConfigParser();ini.read(ROOT/'package/IrisArsenal/IrisArsenal.ini',encoding='utf-8');assert {k for k,v in ini['MoveWeights'].items() if float(v)>0}=={'fire_roll','spiral','earthquake','drill','full_burst','vulcan','pulse','drive','electro_cannon','hammer_combo'}
    moves=json.loads((ROOT/'docs/eight-moves.json').read_text('utf-8'))['moves'];assert all(e['radius']==36 and e['multiplier']==1.5 for e in moves[2]['events'])
    return {'drive':{'range':[0,10000],'radius':9,'length':'same private FCS maximum (10000)','health_events':4,'multiplier_each':1.5,'native_OBB_and_true_convex_shapes':True,'flat_cap_analytic_cases':len(cases),'GPU_envelope':[radial,lo,hi],'C++_algorithm_executed':False},'earthquake':{'style':'source fire variant','source':'IrisExplosion3→SPEL0865→MGEF0866→EXPL086A→explosionwarm0.nif','reference_seconds':[215,217],'health_events':4,'radius':36,'multiplier_each':1.5,'source_mesh_layers':6,'source_seconds':4,'full_Skyrim_NiPSys':False},'reticle':{'flat':True,'layers':2,'reference_reconstruction':True,'verified_original_NIF':False},'pulse_presentation':{'alpha':2.2,'RGB':1.45,'health_changed':False},'AOE':{'native_accurate_sphere_queries':True,'same_tick_fact_cache_capacity':16,'identity_deduplication':True,'health_events_stay_independent':True,'medical_soft_budget':'INI default12/2.5ms; target40ms advisory','query_budget':64,'native_shadow_fallback_Ephnel_parity':False,'FPS_measured':False},'long_beam_blocker':{'streamed_min_cases':15,'kept_world_contacts':1,'health_target_capacity_unchanged':256},'ranged_stall':{'old_source_FCS_gate':360,'new_FCS_and_private_GUN_DATA':10000,'old_log_contains_distance':False,'historical_cause_proven':False,'new_state_change_notices_max':32,'native_safety_gates_preserved':True},'compile':False,'game_tested':False}

if __name__=='__main__':print(json.dumps(verify_cannon_quake(),ensure_ascii=False,indent=2))
