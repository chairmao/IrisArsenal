"""067按PIE/ESP实际引用重建翻滚、全力尾击与电脉；不改变源光刃和伤害。"""
# 070：移除已由AST与跨模块引用核实的未使用导入；原资源生产算法保持。
import copy,json,math
import numpy as np
from safeio import ROOT,put
import drill_particles,fire_burst,fire_optics,fire_coverage,finisher_coverage064
from fx_timeline import timeline
from drive_effects059 import raw_sub,mesh_blob,shader_material,sample,buffers_from_bytes
from drill_finisher import billboard_names
A=ROOT/'package/IrisArsenal/assets'
IDENT=fire_burst.IDENTITY
KEYS=('roll_blast','full_blast','electro_area','electro_burst')

def measure_source(a,path):
    meshes,_=a.a.read_nif(path);meshes=[m for m in meshes if not fire_optics.refractive(m)]
    data=timeline(path,meshes,'SpecialIdle_AreaEffect',a.a.C,a.a.SCALE)
    blocks={b['index']:b for b in a.nr.parse(path)['parsed_blocks']}
    geometry=finisher_coverage064.measure(a,meshes,data['tracks'],blocks,data['duration'],min(1.25,data['duration']))
    layers,record=drill_particles.export(a,path,0,capacity_limit=512,normalize=False)
    # 源MeshEmitter的Ripples在发射期间扩散；只在出生时应用源矩阵，不能让已经发出的火花继续贴着网格。
    for layer in layers:
        if layer['source_parameters']['kind']!='NiPSysMeshEmitter':continue
        indices=layer['source_parameters']['meshes'];assert len(indices)==1
        emitter=indices[0];tr=next((tr for mesh,tr in zip(meshes,data['tracks']) if mesh['index']==emitter),None)
        if tr is None:
            # FireBall的发射网格95本身不渲染，也没有材质；用其真实节点作只读代理追踪出生矩阵。
            # 不能因为可视网格表里没有它而省略源发射动画，更不能把辅助网格画出来。
            node=fire_burst.nodes(path)[emitter];proxy=copy.deepcopy(meshes[0]);proxy.update(index=emitter,name=node['name'],matrix=node['world'],vertices=[[0,0,0]])
            tr=timeline(path,[proxy],'SpecialIdle_AreaEffect',a.a.C,a.a.SCALE)['tracks'][0]
        for p in layer['particles']:
            state=sample(np.asarray(tr['frames']),p[6],data['duration']);M=state[13:].reshape(3,4)
            p[:3]=(M[:,:3]@p[:3]+M[:,3]).tolist()
            # 原法向速度只接受旋转；NiAV缩放已由export的system_scale计入，不能随扩散矩阵再放大。
            rot=M[:,:3].copy();rot/=np.maximum(np.linalg.norm(rot,axis=0),1e-9)
            p[3:6]=(rot@p[3:6]).tolist()
    body=[l for l in layers if l['name']=='pFireBall']
    body_measure=fire_coverage.measure(a,body,np.linspace(.03,record['life']-.02,32)) if body else None
    return dict(path=path,meshes=meshes,data=data,blocks=blocks,layers=layers,record=record,geometry=geometry,body=body_measure)

def fresh_name(key,label,old):
    # 源名称可能含冒号；运行字符串保持，material声明必须完整引用，不能再触发065的继承解析错误。
    return 'IrisArsenal/Source067/'+key+'/'+label+'/'+old.split('/')[-1]

def nif_component(a,key,label,source,scale,speed,delay=0):
    q=copy.deepcopy(source);path=q['path'];d=q['data'];cards=billboard_names(path);out=[]
    for mesh,tr in zip(q['meshes'],d['tracks']):
        p=(np.asarray(mesh['vertices'])@mesh['matrix'][:3,:3].T+mesh['matrix'][:3,3])@a.a.C.T*a.a.SCALE*scale
        normal=np.asarray(mesh['normals'])@np.linalg.inv(mesh['matrix'][:3,:3])@a.a.C.T;normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-9)
        colour=np.asarray(mesh['colours']) if mesh['colours'] else np.ones((len(p),4));uv=np.asarray(mesh['uv'])
        old=a.material(mesh,q['blocks']);name=fresh_name(key,label,old);spec=copy.deepcopy(a.MATS[old])
        # 同族暖色冲击沿用064 Stokes已明确的4倍显示曝光适配；非源值，不造光斑或替换贴图。
        if label=='Warm824':spec['presentation']=[1.,4.]
        if mesh['name'] in cards:spec['burst_card_center']=((p.min(0)+p.max(0))*.5).tolist()
        a.MATS[name]=spec;states=np.asarray(tr['frames']).copy();states[:,[16,20,24]]*=scale
        rows=np.c_[p,normal,colour,uv];out.append(dict(name=name,raw=raw_sub(a.a,name,rows,mesh['triangles']),rows=rows,states=states,duration=d['duration'],speed=speed,delay=delay,mesh=mesh['name'],card_center=spec.get('burst_card_center')))
    for layer in q['layers']:
        old=layer['material'];name=fresh_name(key,label,old);spec=copy.deepcopy(a.MATS[old]);layer['material']=name
        if label=='Warm824':spec['gain']*=4.
        # 对完整源实例作一次空间/时间变换；出生/寿命/速度/重力必须同步，不能只加快可视时钟。
        layer['acceleration']=(np.asarray(layer.get('acceleration',[0,0,0]))*scale*speed**2).tolist();spec['acceleration']=layer['acceleration'];a.MATS[name]=spec
        for p in layer['particles']:
            p[:3]=(np.asarray(p[:3])*scale).tolist();p[3:6]=(np.asarray(p[3:6])*scale*speed).tolist();p[6]=delay+p[6]/speed;p[7]/=speed;p[8]*=scale
        raw,positions=drill_particles.submesh(a,layer);rows=buffers_from_bytes(mesh_blob(a.a,[raw],[[-1]*3,[1]*3]))[0][1]
        out.append(dict(name=name,raw=raw,rows=rows,states=None,duration=q['record']['life']/speed+delay,speed=1,delay=0,mesh=layer['name'],layer=layer))
    return out

def firewave_component(a,key,c,scale,speed):
    # FullBust_End原3F9ED：六曲面及七个ADDN64共享的两份粒子池，完全复用已核实解析器。
    out=[]
    for i,(raw,tr) in enumerate(zip(c['subs'],c['tracks'])):
        old,rows=buffers_from_bytes(mesh_blob(a.a,[raw],[[-1]*3,[1]*3]))[0];rows=rows.copy();name=fresh_name(key,'FireWave',old);spec=copy.deepcopy(a.MATS[old])
        if spec.get('burst_particle'):
            layer=copy.deepcopy(c['record']['render_layers'][i-6]);layer['material']=name
            layer['acceleration']=(np.asarray(layer['acceleration'])*scale*speed**2).tolist();spec['acceleration']=layer['acceleration']
            for p in layer['particles']:
                p[:3]=(np.asarray(p[:3])*scale).tolist();p[3:6]=(np.asarray(p[3:6])*scale*speed).tolist();p[6]/=speed;p[7]/=speed;p[8]*=scale
            a.MATS[name]=spec;raw,positions=drill_particles.submesh(a,layer);rows=buffers_from_bytes(mesh_blob(a.a,[raw],[[-1]*3,[1]*3]))[0][1]
            out.append(dict(name=name,raw=raw,rows=rows,states=None,duration=c['duration']/speed,speed=1,delay=0,mesh=tr['mesh'],layer=layer))
        else:
            rows[:,:3]*=scale
            if 'burst_card_center' in spec:spec['burst_card_center']=(np.asarray(spec['burst_card_center'])*scale).tolist()
            a.MATS[name]=spec;states=np.asarray(tr['frames']).copy();states[:,[16,20,24]]*=scale
            from finisher_sources064 import replace_sub
            raw=replace_sub(raw,old,name,rows)
            out.append(dict(name=name,raw=raw,rows=rows,states=states,duration=c['duration'],speed=speed,delay=0,mesh=tr['mesh']))
    return out

def pack(a,key,parts):
    duration=max(p['duration'] if p['states'] is None else p['delay']+p['duration']/p['speed'] for p in parts)
    samples=min(241,math.ceil(duration*60)+1);times=np.linspace(0,duration,samples);tracks=[];points=[];bound=0
    for p in parts:
        frames=[];rows=p['rows'];points.extend(rows[:,:3])
        for t in times:
            if p['states'] is None:state=np.asarray(IDENT).copy()
            else:
                age=(t-p['delay'])*p['speed'];state=sample(p['states'],age,p['duration']).copy()
                if age<0 or age>=p['duration']:state[3]=0
                M=state[13:].reshape(3,4);q=rows[:,:3]@M[:,:3].T+M[:,3];bound=max(bound,float(np.linalg.norm(q,axis=1).max()))
                if p.get('card_center') is not None:
                    center=M[:,:3]@p['card_center']+M[:,3];bound=max(bound,float(np.linalg.norm(center)+np.linalg.norm(q-center,axis=1).max()))
            frames.append(state.tolist())
        if p['states'] is None:bound=max(bound,float(np.linalg.norm(fire_burst.part_bounds([p['layer']]),axis=1).max()))
        tracks.append(dict(mesh=p['mesh'],frames=frames))
    points=np.asarray(points);bounds=[[-bound]*3,[bound]*3]
    asset=dict(key=key,source='PIE/ESP verified067',materials=[p['name']for p in parts],min=points.min(0).tolist(),max=points.max(0).tolist(),center=((points.max(0)+points.min(0))*.5).tolist(),bound_radius=float(np.linalg.norm(points,axis=1).max()),particle_mesh=True,reference_radius=1,limitations='真实源层组合；统一实例尺度和明确录像时钟适配；非Skyrim ENB/折射/程序闪电运行时')
    curve=dict(duration=duration,samples=samples,peak_radius=bound,bounds=bounds,tracks=tracks)
    return mesh_blob(a.a,[p['raw']for p in parts],bounds),asset,curve

def beam(a,warm_scale):
    # IrisBeam的886链确为beam.nif；保留五层真实曲面，纵向仍到既有前20/R25球的最远面。
    from read_legacy_nif import read_legacy
    path=a.S/'Meshes/SW/Iris/beam.nif';meshes,_=read_legacy(path);d=timeline(path,meshes,'mIdle',a.a.C,a.a.SCALE)
    meshes=a.normalize_beam(meshes,d,True);blocks={b['index']:b for b in a.nr.parse(path)['parsed_blocks']};parts=[]
    for mesh,tr in zip(meshes,d['tracks']):
        p=(np.asarray(mesh['vertices'])@mesh['matrix'][:3,:3].T+mesh['matrix'][:3,3])@a.a.C.T*a.a.SCALE
        p[:,:2]*=25*warm_scale;normal=np.asarray(mesh['normals'])@np.linalg.inv(mesh['matrix'][:3,:3])@a.a.C.T;normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-9)
        col=np.asarray(mesh['colours']) if mesh['colours'] else np.ones((len(p),4));rows=np.c_[p,normal,col,np.asarray(mesh['uv'])]
        old=a.material(mesh,blocks);name=fresh_name('electro_burst','Beam',old);a.MATS[name]=copy.deepcopy(a.MATS[old]);states=np.asarray(tr['frames']).copy()
        S=np.diag([25*warm_scale,25*warm_scale,1]);Si=np.linalg.inv(S)
        for st in states:
            M=st[13:].reshape(3,4);M[:,:3]=S@M[:,:3]@Si;M[:,3]=S@M[:,3]
        parts.append(dict(name=name,raw=raw_sub(a.a,name,rows,mesh['triangles']),rows=rows,states=states,duration=d['duration'],speed=1,delay=0,mesh=mesh['name']))
    return pack(a,'electro_burst',parts)

def apply(a=None):
    if a is None:import author_effects as a
    from muzzle_sources063 import take_curves,append_curve
    doc=json.loads((ROOT/'docs/eight-effects.json').read_text('utf8'));old=copy.deepcopy(a.MATS);a.MATS.update(copy.deepcopy(doc['materials']))
    warm=measure_source(a,a.S/'Meshes/SW/Iris/ShoutAreaExplosionWarm0.nif');fire=measure_source(a,ROOT/'tools/source-cache/FireBallExp01.nif')
    # 与064同一标尺：完整源实例按12方向最小可见R95适配既有球半径；软边/冲击光允许越界，绝不改变伤害球。
    # 透明尾/保守裁剪包围不参与归一，避免再次把范围主体缩成小团。
    warm_scale=1/min(warm['geometry']['radius95_by_view']);warm_speed=2.;fire_scale=1/min(fire['body']['radius95_by_view']);fire_speed=max(2.,fire['body']['age']/.20)
    fw=fire_burst.components(a,0,None);flames=[l for l in fw['record']['layers']if l['name'].startswith('FlamesTall03')];fm=fire_coverage.measure(a,flames,np.linspace(.05,fw['duration']-.05,40));fs=1/min(fm['radius95_by_view']);ft=max(2.,fm['age']/.20)
    parts={}
    parts['roll_blast']=nif_component(a,'roll_blast','Warm824',warm,warm_scale,warm_speed)+nif_component(a,'roll_blast','Fire439C0',fire,fire_scale,fire_speed)+nif_component(a,'roll_blast','Fire6051F',fire,fire_scale,fire_speed,.1)
    parts['full_blast']=nif_component(a,'full_blast','Warm824',warm,warm_scale,warm_speed)+firewave_component(a,'full_blast',fw,fs,ft)
    parts['electro_area']=nif_component(a,'electro_area','Warm824',warm,warm_scale,warm_speed)
    results={key:pack(a,key,items)for key,items in parts.items()};results['electro_burst']=beam(a,warm_scale)
    source_files={'roll_blast':fire['path'],'full_blast':fw['source'],'electro_area':warm['path'],'electro_burst':a.S/'Meshes/SW/Iris/beam.nif'}
    for key,(_,asset,_) in results.items():asset.update(source=str(source_files[key]),sha256=a.a.sha(source_files[key]))
    materials={}
    for key,(blob,asset,curve) in results.items():
        assert 0<len(asset['materials'])<=32 and curve['samples']<=241
        put(A/('iris_fx_'+key+'.mesh'),blob,'067源特效网格','只重建指定三招的实际源层/粒子/曲线，不改光刃或伤害')
        for name in asset['materials']:materials[name]=a.MATS[name]
    text='// 067私有源材质；名称完整引用，避免NIF冒号被解释为继承。\n'
    for name,d in materials.items():
        if d.get('burst_particle'):block=drill_particles.material(name,d,a.TEXTURES)
        else:
            block=shader_material(name,d)
            if 'burst_card_center'in d:block=block.replace('IrisEightVP {}','IrisBurstCardVP { param_named cardCenter float3 '+' '.join('%.9f'%v for v in d['burst_card_center'])+' }')
        prefix='material '+name+'\n';assert block.startswith(prefix)
        text+='material "'+name+'"\n'+block[len(prefix):]
    put(A/'iris_source067.material',text,'067专用材质','源UV/颜色/透明/LUT保持，完全隔离其他招式材质')
    for name,data in a.TEXTURES.items():put(A/name,data,'源贴图缓存','仅真实源像素转换，不绘制新贴图')
    lines=(A/'effects.csv').read_text('utf8').splitlines();out=[lines[0]];i=1
    while i<len(lines):
        row=lines[i].split();end=i+1+int(row[2]);key=row[0]
        if key in results:
            asset=results[key][1];out.append(key+' iris_fx_'+key+'.mesh '+str(len(asset['materials']))+' '+' '.join('%.9f'%v for v in asset['center']+[asset['bound_radius']]));out.extend(asset['materials'])
        else:out.extend(lines[i:end])
        i=end
    put(A/'effects.csv','\n'.join(out)+'\n','067效果表','只替换四条既有记录，总数22不变')
    lines,count=take_curves((A/'effect_curves.csv').read_text('utf8'),set(KEYS))
    for key,(_,asset,curve)in results.items():append_curve(lines,key,curve)
    put(A/'effect_curves.csv','IRIS_FX_CURVES 1 '+str(count+len(results))+'\n'+'\n'.join(lines)+'\n','067源时钟','只替换四个既有效果；所有出生/寿命/运动变换均已烘焙，不再运行时重复加速')
    proof=dict(contract='IRIS_THREE_SOURCE_FX_067',chains=dict(roll=['PIE IrisBackJump SPEL8DB MGEF8DA EXPL439C0 FireBallExp01','MGEF8DC papaStrikeCast2 Spell8CD delay0.1 MGEF8CB EXPL6051F FireBallExp01','same HKX IrisExplosion SPEL824 MGEF812 EXPL810 ShoutAreaExplosionWarm0'],full=['FullBust_End SPEL824 warm','FullBust_End Skyrim3F9ED VoiceFlameWaveProject03 ADDN64 x7 MPSFireWaveFlames'],electro=['IrisBeam SPEL886 MGEF884 PROJ885 beam.nif','same IrisBeam SPEL824 MGEF812 EXPL810 warm']),warm=dict(source=str(warm['path']),sha256=a.a.sha(warm['path']),geometry=warm['geometry'],scale=warm_scale,speed=warm_speed,display_exposure_adapter=4.,display_note='same Stokes-family adapter as064; not original source value; no Skyrim ENB reproduction',particle_count=sum(len(l['particles'])for l in warm['layers'])),fireball=dict(source=str(fire['path']),sha256=a.a.sha(fire['path']),body=fire['body'],scale=fire_scale,speed=fire_speed,script_delay=.1),firewave=dict(source=str(fw['source']),sha256=a.a.sha(fw['source']),measure=fm,scale=fs,speed=ft),limits='程序闪电/折射/Skyrim ENB未移植；真实源确定性发射池，不是逐像素1:1；暖色范围层保留地面薄形，不捏造成球壳；源柔边不等于硬碰撞边界',compiled=False,runtime_verified=False)
    for key,(_,asset,curve) in results.items():
        doc['assets']=[asset if x['key']==key else x for x in doc['assets']];doc['timelines'][key]={k:v for k,v in curve.items()if k!='tracks'}
    doc['materials'].update(materials);doc['source067']=proof
    present={(r['output'],r['source'],r['reference'])for r in doc['textures']}
    for row in a.PROVENANCE:
        key=(row['output'],row['source'],row['reference'])
        if key not in present:doc['textures'].append(row);present.add(key)
    put(ROOT/'docs/eight-effects.json',json.dumps(doc,ensure_ascii=False,indent=2),'067源证据元数据','记录三个招式真正链、时钟和范围适配，其他asset记录保持')
    put(ROOT/'docs/source-effects-067.json',json.dumps(proof,ensure_ascii=False,indent=2),'067来源与范围证据','记录实际PIE/ESP/NIF引用及范围/时钟，不宣称GPU实测')
    a.MATS.clear();a.MATS.update(old)
if __name__=='__main__':apply()
