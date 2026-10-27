"""EXDrill2严格单骨蒙皮离线展开；源AnimObjectA/B相对WEAPON曲线，不写角色骨骼。"""
import copy,math,struct,json
import numpy as np
from nif_reader import Reader
from fx_timeline import raw_blocks,rotation

def transform(r):
    m=np.eye(4);m[:3,:3]=np.asarray(r.read('9f')).reshape(3,3);m[:3,3]=r.read('3f');m[:3,:3]*=r.read('f');return m

def read_meshes(path):
    # 对照NifTools SSE100定义。只接受本资产每形状一个骨、权重1；其他蒙皮明确拒绝。
    raw,strings=raw_blocks(path);nodes={};shaders={};textures={};shapes=[]
    for i,(kind,data) in raw.items():
        r=Reader(data)
        if kind in ('NiNode','BSFadeNode','BSTriShape'):
            name=strings[r.read('I')];extras=[r.read('i') for _ in range(r.read('I'))];r.read('i');r.read('I')
            pos=r.read('3f');rot=r.read('9f');scale=r.read('f');r.read('i')
            if kind!='BSTriShape':nodes[i]=name;continue
            r.read('4f');skin,shader,alpha=r.read('3i');desc=r.read('Q');nt,nv=r.read('2H');size=r.read('I')
            assert desc==0x5b0007065040a and nt==nv==size==0 and alpha==-1
            assert r.read('I')==0;r.done()
            shapes.append((i,name,skin,shader))
        elif kind=='BSShaderTextureSet':
            textures[i]=[r.string() for _ in range(r.read('I'))];r.done()
        elif kind=='BSLightingShaderProperty':
            typ=r.read('I');r.read('I');[r.read('i') for _ in range(r.read('I'))];r.read('i')
            flags=r.read('2I');off=r.read('2f');scale=r.read('2f');tex=r.read('i');emission=r.read('3f');mult=r.read('f');clamp=r.read('I');alpha=r.read('f')
            refraction=r.read('f');gloss=r.read('f');specular=r.read('3f');strength=r.read('f');light=r.read('2f');r.done()
            assert typ in (0,2)
            shaders[i]={'texture':tex,'emissive':emission,'emissive_mult':mult,'alpha':alpha,'uv_offset':off,'uv_scale':scale,'shader_type':typ,'clamp_mode':clamp,'flags':flags,'refraction':refraction,'glossiness':gloss,'specular':specular,'specular_strength':strength,'lighting_effect':light}
    output=[]
    for index,name,skin,shader in shapes:
        r=Reader(raw[skin][1]);data_id,part_id,root=r.read('3i');assert r.read('I')==1
        bone=r.read('i');assert nodes[bone] in ('AnimObjectA','AnimObjectB')
        parts=r.read('I');assert parts==1;r.read('2H');r.done()
        r=Reader(raw[data_id][1]);base=transform(r);assert np.allclose(base,np.eye(4),atol=1e-5)
        assert r.read('I')==1 and r.read('B')==1
        bind=transform(r);r.read('4f');count=r.read('H');weights=[r.read('Hf') for _ in range(count)];r.done()
        assert sorted(v[0] for v in weights)==list(range(count)) and all(abs(v[1]-1)<1e-6 for v in weights)
        r=Reader(raw[part_id][1]);assert r.read('I')==1
        size,stride=r.read('2I');desc=r.read('Q');assert stride==40 and desc==0x5b0007065040a and size==count*stride
        buffer=r.data[r.pos:r.pos+size];r.pos+=size
        nv,nt,nb,ns,nw=r.read('5H');assert nv==count and nb==1 and ns==0 and nw==4 and r.read('H')==0
        assert r.read('B')==1;vertex_map=r.read(str(nv)+'H');assert vertex_map==list(range(nv))
        assert r.read('B')==1
        pw=np.asarray(r.read(str(nv*nw)+'f')).reshape(nv,nw);assert np.allclose(pw[:,0],1) and np.allclose(pw[:,1:],0)
        assert r.read('B')==1;tris=np.asarray(r.read(str(nt*3)+'H')).reshape(nt,3)
        assert r.read('B')==1;indices=r.read(str(nv*nw)+'B');assert max(indices)==0
        r.read('B');r.read('B');assert r.read('Q')==desc
        copies=np.asarray(r.read(str(nt*3)+'H')).reshape(nt,3);r.done();assert np.array_equal(tris,copies) and tris.max()<nv
        vertices=[];normals=[];uv=[]
        for k in range(nv):
            q=Reader(buffer[k*stride:(k+1)*stride]);vertices.append(q.read('3f'));q.read('f');uv.append(q.read('2e'));normals.append([(v/127.5-1) for v in q.read('4B')[:3]])
            q.read('4B');w=q.read('4e');bi=q.read('4B');q.done();assert abs(w[0]-1)<1e-6 and max(bi)==0
        sh=shaders[shader]
        output.append({'index':index,'name':name,'bone':nodes[bone],'vertices':vertices,'normals':normals,'uv':uv,'colours':[],'triangles':tris.tolist(),'matrix':bind,'shader':shader,'shader_data':sh,'textures':textures[sh['texture']],'alpha_data':None})
    assert len(output)==10
    return output

def source_world(author,clip,rig,t):
    # 与身体作者相同的左右骨名别名；这里只算源矩阵，不改Kenshi骨架。
    tracks={name:i for i,name in enumerate(clip.bone_names)};out=[]
    aliases={'Weapon':'WEAPON'}
    for side in ('L','R'):
        for base,tag in [('Thigh','Thg'),('Calf','Clf'),('Foot','ft '),('Toe0','Toe'),('Clavicle','Clv'),('UpperArm','Uar'),('Forearm','Lar'),('Hand','Hnd')]:
            aliases['NPC '+side+' '+base+' ['+side+tag+']']='NPC '+base+' ['+tag+'].'+side
    for i,name in enumerate(rig.bones):
        p=rig.reference_pose[i];j=tracks.get(aliases.get(name,name))
        if j is None:pos=np.asarray(p.translation);q=np.asarray(p.rotation)
        else:
            tr=clip.tracks[j];pos=np.asarray(author.interp(tr.translations,t,clip.duration));q=np.asarray(author.interp(tr.rotations,t,clip.duration,True))
        m=np.eye(4);m[:3,:3]=rotation((q[3],q[0],q[1],q[2]));m[:3,3]=pos;parent=rig.parents[i]
        out.append(m if parent<0 else out[parent]@m)
    return out

def build(a):
    from anim_skyrim import load_skyrim_animation,load_skyrim_skeleton
    from safeio import ROOT,put
    source=a.S/'Meshes/SW/Iris/EXDrill2.nif'
    spec=json.loads((ROOT/'docs/eight-moves.json').read_text('utf-8'))['moves'][3]
    cue={e['text']:e['time'] for e in spec['source_events']}
    begin=cue['PIE.$IrisEXDrill2']+.02;end=cue['PIE.$IrisEXDrillOFF'];duration=end-begin
    clip=load_skyrim_animation(spec['sources'][0]);rig=load_skyrim_skeleton(str(a.a.SKEL))
    meshes=read_meshes(source);H=np.eye(4);H[:3,:3]=a.a.C*a.a.SCALE;Hi=np.linalg.inv(H)
    samples=round(duration*60)+1;times=np.linspace(begin,end,samples)
    worlds=[source_world(a.a,clip,rig,float(t)) for t in times]
    weapon=rig.bones.index('Weapon');ids={n:rig.bones.index(n) for n in ('AnimObjectA','AnimObjectB')}
    tracks=[];points=[];defaults=[];audit=[]
    # 源每翼完整网格在每个采样时刻的包围中心各算一次，再取中点；不拿旋转骨原点充当翼片中心。
    fan_bounds=[{name:[np.full(3,np.inf),np.full(3,-np.inf)] for name in ids} for _ in times]
    for mesh in meshes:
        p=(np.asarray(mesh['vertices'])@mesh['matrix'][:3,:3].T+mesh['matrix'][:3,3])@a.a.C.T*a.a.SCALE;defaults.append(p)
        states=[]
        for frame,world in enumerate(worlds):
            delta=H@np.linalg.inv(world[weapon])@world[ids[mesh['bone']]]@Hi
            state=[*mesh['shader_data']['emissive'],1,0,0,1,1,1,1,0,1,1]+delta[:3].reshape(-1).tolist()
            states.append(state);q=p@delta[:3,:3].T+delta[:3,3]
            # 只累积逐帧包围值，避免源高模×全时间流保留数百MB临时顶点。
            points.extend([q.min(0),q.max(0)])
            fan=fan_bounds[frame][mesh['bone']];fan[0]=np.minimum(fan[0],q.min(0));fan[1]=np.maximum(fan[1],q.max(0))
        tracks.append({'mesh':mesh['name'],'frames':states})
        audit.append({'mesh':mesh['name'],'bone':mesh['bone'],'vertices':len(p),'triangles':len(mesh['triangles']),'weights':'all1, one source bone; exact rigid extraction'})
    centers=[sum((np.asarray(lo)+np.asarray(hi))*.5 for lo,hi in f.values())*.5 for f in fan_bounds]
    assert np.isfinite(centers).all()
    put(a.A/'wing_centers.csv','IRIS_WING_CENTERS 1 %d %.9f %.9f\n'%(samples,begin,end)+'\n'.join(' '.join('%.9f'%x for x in p) for p in centers)+'\n','源双翼对称中心','与原翼片同采样/同单位/同时间，运行时插值后乘当前真实武器矩阵；不跟踪目标')
    # 原翼片九形状镜面强度10、一个为1；逐形状保留，不能统一降级为简化明暗。
    for mesh in meshes:
        sh=mesh['shader_data'];mesh['wing_source_metal']={'specular':sh['specular'],'strength':sh['specular_strength'],'glossiness':sh['glossiness']}
    raw,mats,p=a.mesh_bytes(meshes,{})
    q=np.asarray(points);lo=np.minimum(p.min(0),q.min(0));hi=np.maximum(p.max(0),q.max(0));peak=float(np.linalg.norm(np.maximum(np.abs(lo),np.abs(hi))))
    raw=raw[:-34]+a.a.chunk(0x9000,struct.pack('<7f',*lo,*hi,peak))
    put(a.A/'iris_fx_drill_wings.mesh',raw,'源终结翼片','EXDrill2十形状精确单骨转刚体；相对真实WEAPON播放AnimObjectA/B源开合轨道')
    asset={'key':'drill_wings','source':str(source),'sha256':a.a.sha(source),'materials':mats,'min':p.min(0).tolist(),'max':p.max(0).tolist(),'center':((p.max(0)+p.min(0))*.5).tolist(),'bound_radius':float(np.linalg.norm(p-(p.max(0)+p.min(0))*.5,axis=1).max()),'layers':audit,'source_window':[begin,end],'limitations':'本资产全部单骨权重1，精确导出；不是通用多骨蒙皮支持，不新增伤害'}
    curve={'duration':duration,'samples':samples,'peak_radius':peak,'bounds':[lo.tolist(),hi.tolist()],'tracks':tracks,'source_window':[begin,end],'source_weapon_relative':True}
    put(ROOT/'docs/drill-wings-038.json',json.dumps({'asset':asset,'curve':{k:v for k,v in curve.items() if k!='tracks'}},ensure_ascii=False,indent=2),'翼片来源/时钟证据','原10形状、两个源动画对象、相对武器坐标及真实开合窗口')
    return asset,curve
