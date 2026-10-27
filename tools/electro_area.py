"""049电脉：原824三层曲面＋真实275火花；同一可见半径与源相对标尺。"""
import copy,struct,json
import numpy as np
import drill_particles,drill_finisher
from safeio import ROOT

def source(e):
    if hasattr(e,"_electro051_source"):return copy.deepcopy(e._electro051_source)
    a=e.a;path=e.S/'Meshes/SW/Iris/ShoutAreaExplosionWarm0.nif';meshes,_=a.read_nif(path)
    excluded=[x['name'] for x in meshes if x['name'].startswith('GeoSphere')]
    meshes=[x for x in meshes if not x['name'].startswith('GeoSphere')]
    blocks=drill_finisher.source_blocks(path);d=e.timeline(path,meshes,'SpecialIdle_AreaEffect',a.C,a.SCALE)
    # 可见扩散层的半透明以上阶段才是显示标尺；透明尾仍进入裁剪包围，不能再把它用来缩小画面。
    visible=[];all_points=[]
    for mesh,tr in zip(meshes,d['tracks']):
        p=drill_finisher.points(e,mesh)
        for state in tr['frames']:
            m=np.asarray(state[13:]).reshape(3,4);q=p@m[:,:3].T+m[:,3];all_points.append(q)
            if state[3]>=.5 and max(state[:3])>=.25:visible.append(q)
    geometric_radius=float(np.linalg.norm(np.concatenate(visible)[:,[0,2]],axis=1).max());assert geometric_radius>0
    # 051旧133.3是整片几何的外缘，大片DarkSwirls低亮像素把真正火焰主体缩成小团。
    # 保留原网格/曲线/三层相对关系，以真实纹理、顶点alpha、LUT和源falloff测得的发亮主体统一到R25。
    # 同一尺度也供beam横截面和275源火花使用；不逐层放大、不造新火焰，不改变伤害球。
    from electro_coverage051 import measure
    radius,calibration=measure(e,meshes,blocks,d);d['source_coverage051']=calibration
    d['source_coverage051']['old_geometric_radius']=geometric_radius
    result=(path,meshes,blocks,d,radius,excluded);e._electro051_source=copy.deepcopy(result);return result

def beam_scale(e):
    # 范围R25和beam原横截面统一从同一NIF坐标单位换算；不再保留未换算的9.7宽光柱。
    return 25/source(e)[4]

def build(e):
    a=e.a;path,meshes,blocks,d,radius,excluded=source(e);H=np.eye(4);H[:3,:3]=a.C*a.SCALE
    N=np.diag([1/radius]*3+[1]);Ni=np.linalg.inv(N);subs=[];mats=[];defaults=[];animated=[];billboard=drill_finisher.billboard_names(path);card_radius=0
    for mesh,tr in zip(meshes,d['tracks']):
        mesh['matrix']=np.linalg.inv(H)@N@H@mesh['matrix']
        raw,names,p=e.mesh_bytes([mesh],blocks);offset=raw.index(b'\n')+1+7;kind,size=struct.unpack_from('<HI',raw,offset);assert kind==0x4000
        # 只恢复原NiBillboardNode继承的Glow；三维扩散/烟气保持原曲面，不重新画一个AOE圈。
        spec=e.MATS[names[0]]
        if mesh['name'] in billboard:
            spec['burst_card_center']=((p.min(0)+p.max(0))*.5).tolist()
        for state in tr['frames']:
            m=np.eye(4);m[:3]=np.asarray(state[13:]).reshape(3,4);m=N@m@Ni;state[13:]=m[:3].reshape(-1).tolist()
            q=p@m[:3,:3].T+m[:3,3];animated.extend(q)
            if mesh['name'] in billboard:
                pivot=np.asarray(spec['burst_card_center'])@m[:3,:3].T+m[:3,3];card_radius=max(card_radius,float(np.linalg.norm(pivot)+np.linalg.norm(q-pivot,axis=1).max()))
        subs.append(raw[offset:offset+size]);mats.extend(names);defaults.extend(p)
    layers,record=drill_particles.export(e,path,0,capacity_limit=512)
    assert len(layers)==1 and layers[0]['source_capacity']==302 and len(layers[0]['particles'])==275
    ripple=next(tr for tr in d['tracks'] if tr['mesh']=='Ripples:0');source_peak=record['source_peak'];particle_bounds=[]
    for layer in layers:
        for particle in layer['particles']:
            # NiPSysMeshEmitter来自正在扩散的Ripples网格，必须按出生帧取其原动画。
            # 输出曲线已归一，先还原到源空间再取出生点；法向只旋转，发射速度不乘网格膨胀尺度。
            t=particle[6];u=np.clip(t/d['duration']*(d['samples']-1),0,d['samples']-1);lo=int(u);hi=min(d['samples']-1,lo+1)
            state=np.asarray(ripple['frames'][lo])*(1-(u-lo))+np.asarray(ripple['frames'][hi])*(u-lo)
            unit=np.eye(4);unit[:3]=state[13:].reshape(3,4);matrix=Ni@unit@N
            p=np.asarray(particle[:3])*source_peak;v=np.asarray(particle[3:6])*source_peak
            normal=np.linalg.inv(matrix[:3,:3]).T@v;normal*=np.linalg.norm(v)/max(1e-9,np.linalg.norm(normal))
            particle[:3]=((matrix[:3,:3]@p+matrix[:3,3])/radius).tolist();particle[3:6]=(normal/radius).tolist();particle[8]*=source_peak/radius
            extent=particle[8]*max(layer['size_curve'])*2**.5
            for age in (0,particle[7]):
                center=np.asarray(particle[:3])+np.asarray(particle[3:6])*age
                for sign in __import__('itertools').product((-1,1),repeat=3):particle_bounds.append(center+np.asarray(sign)*extent)
        layer['acceleration']=(np.asarray(layer['acceleration'])*source_peak/radius).tolist();e.MATS[layer['material']]['acceleration']=layer['acceleration']
        raw,p=drill_particles.submesh(e,layer);subs.append(raw);mats.append(layer['material']);defaults.extend(p)
        identity=[1,1,1,1,0,0,1,1,1,1,0,1,1,1,0,0,0,0,1,0,0,0,0,1,0]
        d['tracks'].append({'mesh':layer['name'],'frames':[identity[:] for _ in range(d['samples'])]})
    p=np.asarray(defaults);q=np.concatenate([p,np.asarray(animated),np.asarray(particle_bounds)]);bound=max(card_radius,float(np.linalg.norm(q,axis=1).max()));low=np.minimum(q.min(0),-bound);high=np.maximum(q.max(0),bound)
    d.update(bounds=[low.tolist(),high.tolist()],peak_radius=bound,source_normalization={'source_horizontal_radius':radius,'target_horizontal_radius':1,'uniform_xyz':True,'visible_alpha_min':.5,'visible_rgb_min':.25,'excluded_refraction_helpers':excluded})
    data=b'\x00\x10[MeshSerializer_v1.41]\n'+a.chunk(0x3000,b'\0'+b''.join(subs)+a.chunk(0x9000,struct.pack('<7f',*low,*high,bound)))
    e.put(e.A/'iris_fx_electro_area.mesh',data,'电脉原范围爆发','三层源曲面/原billboard/275原火花，保留原纹理颜色时间；仅按源可见扩散半径适配R25')
    e.put(ROOT/'docs/electro-source-049.json',json.dumps({'source':str(path),'sha256':a.sha(path),'visible_source_radius':radius,'world_scale':25/radius,'source_billboards':sorted(billboard),'coverage051':d['source_coverage051'],'particle':record,'serialized_particle_layers':layers,'missing':['屏幕折射','完整风场/拖曳/湍流'],'GPU_tested':False},ensure_ascii=False,indent=2),'电脉源链校准证据','原NiPSys容量/出生率/发射网格及实际序列化粒子；未用自拟图形代替')
    return {'key':'electro_area','source':str(path),'sha256':a.sha(path),'materials':mats,'min':p.min(0).tolist(),'max':p.max(0).tolist(),'center':((p.max(0)+p.min(0))*.5).tolist(),'bound_radius':float(np.linalg.norm(p-(p.max(0)+p.min(0))*.5,axis=1).max()),'particle_mesh':True,'source_chain':['$IrisBeam','SPEL824','MGEF812','EXPL810'],'excluded_refraction_helpers':excluded,'limitations':'原三层曲面＋275源火花；原Glow朝相机，原色/渐变/UV/出生时序；未执行屏幕折射/完整风场，前20/R25伤害球与朝向不变'},d
