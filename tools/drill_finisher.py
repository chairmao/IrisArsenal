"""037钻天破终结：原ALS蓝白电离先出现，再播放独立SW火焰爆炸；无地震喷流。"""
import struct,json,numpy as np
import nif_reader as nr
from fx_timeline import timeline
from safeio import ROOT,put
import drill_particles
import drill_volume
import fire_burst
from fx_timeline import raw_blocks
from nif_reader import Reader

def source_blocks(path):
    blocks={x['index']:x for x in nr.parse(path)['parsed_blocks']}
    for seq in list(blocks.values()):
        for cb in seq.get('controlled_blocks',[]):
            if cb['controller'] in blocks:blocks[cb['controller']]['interpolator']=cb['interpolator']
    return blocks

def points(a,mesh):return (np.asarray(mesh['vertices'])@mesh['matrix'][:3,:3].T+mesh['matrix'][:3,3])@a.a.C.T*a.a.SCALE

def unit_group(a,meshes,tracks):
    peak=0
    for mesh,tr in zip(meshes,tracks):
        p=points(a,mesh);peak=max(peak,float(np.linalg.norm(p,axis=1).max()))
        for s in tr['frames']:
            m=np.asarray(s[13:]).reshape(3,4);peak=max(peak,float(np.linalg.norm(p@m[:,:3].T+m[:,3],axis=1).max()))
    assert peak>0
    for mesh,tr in zip(meshes,tracks):
        mesh['matrix'][:3]/=peak
        for s in tr['frames']:s[16]/=peak;s[20]/=peak;s[24]/=peak
    return peak

def billboard_names(path):
    # 两层ALS闪光在原NIF挂在NiBillboardNode下；丢掉这条继承会把相机闪光画成贴地薄片。
    raw,strings=raw_blocks(path);nodes={};parents={}
    for i,(kind,data) in raw.items():
        if kind not in ('BSFadeNode','NiNode','NiBillboardNode','BSTriShape'):continue
        r=Reader(data);name,ctl,m=drill_particles.av(r,strings)
        children=[r.read('i') for _ in range(r.read('I'))] if kind!='BSTriShape' else []
        nodes[i]=(kind,name)
        for child in children:parents[child]=i
    names=set()
    for i,(kind,name) in nodes.items():
        if kind!='BSTriShape':continue
        at=i
        while at in parents:
            at=parents[at]
            if nodes[at][0]=='NiBillboardNode':names.add(name);break
    return names

def build(a):
    # 纠正旧缺失结论：原资产在依赖的meshes/ALS，不在meshes/RimMagic。两相按录像明确错开。
    blue=a.ELDEN/'meshes/ALS/ALSEXP.nif';fire=a.ELDEN/'meshes/RimMagic/SW_FireExplosion.nif'
    meshes,_=a.a.read_nif(blue);assert len(meshes)==3
    billboard=billboard_names(blue);assert {'Flash02:1','Flash02:0'}<=billboard
    doc=timeline(blue,meshes,'SpecialIdle_AreaEffect',a.a.C,a.a.SCALE);unit_group(a,meshes,doc['tracks']);blocks=source_blocks(blue)
    sparks,blue_record=drill_particles.export(a,blue,0,.52)
    fire_components=fire_burst.components(a,.56,'drill');fire_record=fire_components['record']
    assert len(sparks)==1 and len(fire_record['layers'])==14
    fields,field_record=drill_volume.build(a)
    # 原环以前只覆盖约十余单位；以可见阶段XZ半径归一到1，随同一R120放大。
    ring=next(i for i,m in enumerate(meshes) if m['name']=='Torus01:0');rp=points(a,meshes[ring]);reach=0
    for st in doc['tracks'][ring]['frames']:
        if st[3]<.2:continue
        m=np.asarray(st[13:]).reshape(3,4);q=rp@m[:,:3].T+m[:,3];reach=max(reach,float(np.linalg.norm(q[:,[0,2]],axis=1).max()))
    assert reach>0;factor=1/reach;meshes[ring]['matrix'][:3]*=factor
    for st in doc['tracks'][ring]['frames']:
        for k in (16,20,24):st[k]*=factor
    duration=max(.52,blue_record['life'],fire_components['duration'])
    samples=round(duration*30)+1;assert duration<=8 and samples<=241
    # 原序列3秒含长透明尾部；旧代码将整段压进0.52秒，可见闪光只剩约0.1秒。
    # 先量出有颜色且有alpha的源有效窗，再映射到蓝相，保留淡出而不增加总寿命/伤害。
    original=np.asarray([tr['frames'] for tr in doc['tracks']]);visible=(original[:,:,3]>.01)&(np.max(original[:,:,:3],axis=2)>.01)
    last=max(np.flatnonzero(visible.any(axis=0)))+1
    blue_source_end=min(doc['duration'],last/(doc['samples']-1)*doc['duration'])
    assert .1<blue_source_end<doc['duration']
    subs=[];default=[];animated=[];names=[];tracks=[];card_radius=0
    for mesh,tr in zip(meshes,doc['tracks']):
        old=np.asarray(tr['frames']);frames=[]
        for t in np.linspace(0,duration,samples):
            u=min(1,t/.52)*blue_source_end/doc['duration']*(len(old)-1);lo=int(u);hi=min(len(old)-1,lo+1);v=old[lo]*(1-(u-lo))+old[hi]*(u-lo)
            if t>=.52:v[3]=0
            frames.append(v.tolist())
        # 30Hz重采样会略过源环最大帧；按实际输出的可见矩阵再校准，避免R120边界又被采样缩回。
        if mesh['name']=='Torus01:0':
            p=points(a,mesh);serialized_reach=0
            for st in frames:
                if st[3]<.2:continue
                m=np.asarray(st[13:]).reshape(3,4);q=p@m[:,:3].T+m[:,3]
                serialized_reach=max(serialized_reach,float(np.linalg.norm(q[:,[0,2]],axis=1).max()))
            assert serialized_reach>0
            for st in frames:st[13:]=[x/serialized_reach for x in st[13:]]
        # 只去掉其错误白底：源无纹理的Flash02:1用原羽化遮罩，其他ALS纹理/渐变保持。
        if not mesh['shader_data']['effect']['source_texture']:
            mesh['shader_data']['effect']['source_texture']='textures/effects/GlowSlightFlash.dds'
        raw,mats,p=a.mesh_bytes([mesh],blocks)
        offset=raw.index(b'\n')+1+7;typ,size=struct.unpack_from('<HI',raw,offset);assert typ==0x4000
        # 只给原本就朝向相机的两层恢复billboard；环形冲击层保留三维源几何/姿态。
        spec=a.MATS[mats[0]];spec['ion_blue']=True;spec['presentation']=[.65,1.8]
        if mesh['name'] in billboard:
            assert np.ptp(p[:,1])<1e-4
            spec['burst_card_center']=((p.min(0)+p.max(0))*.5).tolist()
        subs.append(raw[offset:offset+size]);names.extend(mats);default.extend(p);tracks.append({'mesh':mesh['name'],'frames':frames})
        for state in frames:
            m=np.asarray(state[13:]).reshape(3,4);moved=p@m[:,:3].T+m[:,3];animated.extend(moved)
            if 'burst_card_center' in spec:
                pivot=np.asarray(spec['burst_card_center'])@m[:,:3].T+m[:,3]
                card_radius=max(card_radius,float(np.linalg.norm(pivot)+np.linalg.norm(moved-pivot,axis=1).max()))
    identity=[1,1,1,1,0,0,1,1,1,1,0,1,1,1,0,0,0,0,1,0,0,0,0,1,0]
    for layer in sparks+fields:
        sub,p=drill_particles.submesh(a,layer);subs.append(sub);names.append(layer['material']);default.extend(p)
        tracks.append({'mesh':layer['name'],'frames':[identity[:] for _ in range(samples)]})
    # 共享火焰组件拥有同一绝对后效时钟；这里合入子网格/轨道，不生成第二个爆炸事件。
    assert samples==fire_components['samples'] and abs(duration-fire_components['duration'])<1e-8
    subs.extend(fire_components['subs']);names.extend(fire_components['materials']);default.extend(fire_components['points']);tracks.extend(fire_components['tracks'])
    default=np.asarray(default)
    bounds=np.concatenate([np.asarray(animated),np.asarray(blue_record['bounds']),np.asarray(fire_record['bounds']),np.asarray(field_record['bounds']),default])
    lo=bounds.min(0);hi=bounds.max(0);bound=max(card_radius,float(np.linalg.norm(bounds,axis=1).max()))
    # billboard可在任意镜头下旋转；球半径保留真实源包络，AABB按球外扩，不能被旧水平薄片包围盒裁掉。
    lo=np.minimum(lo,-bound);hi=np.maximum(hi,bound)
    raw=b'\x00\x10[MeshSerializer_v1.41]\n'+a.a.chunk(0x3000,b'\0'+b''.join(subs)+a.a.chunk(0x9000,struct.pack('<7f',*lo,*hi,bound)))
    put(a.A/'iris_fx_drill_blast.mesh',raw,'原ALS→原FireWave爆炸分层','原ALS电离层透明化，0.52秒结束；0.56秒后原FireWave六曲面/七个源附加发射体；无巨型火焰卡片，不复用地震')
    center=(default.min(0)+default.max(0))*.5
    source_layers=[{'file':str(p),'sha256':a.a.sha(p)} for p in (blue,fire_components['source'])]
    asset={'key':'drill_blast','source':str(blue),'sha256':a.a.sha(blue),'source_layers':source_layers,'materials':names,'min':default.min(0).tolist(),'max':default.max(0).tolist(),'center':center.tolist(),'bound_radius':float(np.linalg.norm(default-center,axis=1).max()),'particle_mesh':True,'phase_timing':{'blue_end':.52,'fire_begin':.56},'radius_contract':'unit_sphere_matches_damage_radius','reference_radius':1,'coverage_particles':49,'limitations':'采用原ALS与FullBust_End真实FireWave六曲面/七个原附加节点；源曲面/附加点/初始角度/匀强重力/图集与五点尺寸；固定随机种子，未完整模拟受控力、拖曳/湍流/折射；非地震'}
    curve={'duration':duration,'samples':samples,'peak_radius':bound,'bounds':[lo.tolist(),hi.tolist()],'tracks':tracks,'source_adaptation':source_layers}
    put(ROOT/'docs/drill-burst-041.json',json.dumps({'source_layers':source_layers,'blue':blue_record,'fire':fire_record,'phase_timing':asset['phase_timing'],'blue_source_visible_end':blue_source_end,'visibility_revision':'041-RangeMetal','coverage':field_record,'ring_visible_radius':1,'duration':duration,'runtime_verified':False},ensure_ascii=False,indent=2),'原终结发射器证据','保留原源/矩形32帧图集/有界发射/曲面；降低蓝相遮挡，火焰与翻滚共享材质，蓝火不同时出生')
    return asset,curve
