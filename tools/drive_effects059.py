"""059只替换极致驱动beam/ion：真实EXanim1附件与原枪口链，外部CC0光流不冒称原招已有。"""
from pathlib import Path
import copy,json,math,struct,zipfile
from io import BytesIO
import numpy as np
from safeio import ROOT,put
from effect_data059 import buffers,curves
from fx_timeline import timeline
from read_drive059 import read_parts
import drill_particles,fire_optics

A=ROOT/'package/IrisArsenal/assets';CACHE=ROOT/'tools/source-cache/drive059'
MU=np.array([1.807138657,0,8.534358047]);FIRE=3.1665399074554443;BLUE_END=FIRE+.56;END=5.5
IDENT=[1,1,1,1,0,0,1,1,1,1,0,1,1]+np.eye(4)[:3].reshape(-1).tolist()

def raw_sub(a,name,vertices,triangles):
    v=np.asarray(vertices,dtype='<f4');idx=np.asarray(triangles,dtype='<u2').reshape(-1);assert v.shape[1]==12 and len(v)<65536 and idx.max()<len(v)
    decl=a.chunk(0x5100,b''.join(a.chunk(0x5110,struct.pack('<5H',0,t,s,o,0)) for t,s,o in [(2,1,0),(2,4,12),(3,5,24),(1,7,40)]))
    geom=a.chunk(0x5000,struct.pack('<I',len(v))+decl+a.chunk(0x5200,struct.pack('<HH',0,48)+a.chunk(0x5210,v.tobytes())))
    return a.chunk(0x4000,name.encode()+b'\n'+struct.pack('<?I?',False,len(idx),False)+idx.tobytes()+geom)

def mesh_blob(a,subs,bounds):
    p=np.asarray(bounds);return b'\x00\x10[MeshSerializer_v1.41]\n'+a.chunk(0x3000,b'\0'+b''.join(subs)+a.chunk(0x9000,struct.pack('<7f',*p.min(0),*p.max(0),np.linalg.norm(p,axis=1).max())))

def transform_state(s,frame):
    s=list(s);mat=np.eye(4);mat[:3]=np.asarray(s[13:]).reshape(3,4);mat=frame@mat@np.linalg.inv(frame);s[13:]=mat[:3].reshape(-1).tolist();return s

def sample(states,t,duration):
    k=np.clip(t/duration*(len(states)-1),0,len(states)-1);lo=int(k);hi=min(len(states)-1,lo+1);return np.asarray(states[lo])*(1-(k-lo))+np.asarray(states[hi])*(k-lo)

def shader_material(name,d):
    v=lambda x:' '.join('%.9f'%float(z) for z in x)
    return ('material '+name+'\n{ technique { pass {\n lighting off\n depth_check on\n depth_write off\n cull_hardware none\n scene_blend '+d['blend']+'\n vertex_program_ref IrisEightVP {}\n fragment_program_ref IrisEightFP {\n param_named_auto clock custom 1\n param_named_auto sourceTint custom 2\n param_named_auto sourceUV custom 3\n param_named_auto sourceMisc custom 4\n param_named_auto sourceFalloff custom 8\n param_named uvBase float4 '+v(d['uv'])+'\n param_named uvFlow float4 '+v(d['scroll']+[0,0])+'\n param_named tint float4 '+v(d['emission']+[d['alpha']])+'\n param_named flags float4 '+v([int(d['effect']),int(d['opaque']),int(d['grey_color']),int(d['grey_alpha'])])+'\n param_named vertexFlags float4 '+v([int(d['vertex_color']),int(d['vertex_alpha']),int(d['use_falloff']),d['alpha_cutoff']])+'\n param_named effectParams float4 '+v([d['gain'],int(d['has_source']),int(d['has_palette']),0])+'\n param_named presentation float4 '+v(d.get('presentation',[1,1])+[int(d.get('beam_colour',False)),int(d.get('ion_blue',False))])+'\n param_named falloff float4 '+v(d['falloff'])+'\n }\n texture_unit { texture '+d['diffuse']+' }\n texture_unit { texture '+d['palette']+'\n tex_address_mode clamp\n }\n } } }\n')

def beam(a):
    # 使用已下载并查看的CC0 Laser1/FlamesTexture原像素；闭合圆柱而非旧环状几何或放大的球。
    z=zipfile.ZipFile(CACHE/'beamvfxassets.zip')
    for src,dst in [('Laser1.png','iris_drive059_laser.png'),('FlamesTexture.png','iris_drive059_flow.png')]:put(A/dst,z.read('BeamVFXAssets/'+src),'CC0原始光流纹理','原PNG字节，不重新绘制或放大像素')
    subs=[];names=[];allp=[]
    for layer,radius in enumerate((1.,.72,.32)):
        name='IrisArsenal/Drive059/Stream'+str(layer);a.MATS[name]={'drive059_stream':True,'layer':layer,'diffuse':'iris_drive059_laser.png','texture':'iris_drive059_flow.png','license':'CC0-1.0'};verts=[];tri=[]
        for j in range(25):
            zz=j/24
            for k in range(65):
                angle=k*math.tau/64;x,y=radius*math.cos(angle),radius*math.sin(angle)
                verts.append([x,y,zz,math.cos(angle),math.sin(angle),0,1,1,1,1,zz,k/64]);allp.append([x,y,zz])
        for j in range(24):
            for k in range(64):i=j*65+k;tri.extend([[i,i+65,i+66],[i,i+66,i+1]])
        # 平端封口与原生平端圆柱一致，不让可见锥尖伸出墙后；近端被原枪口火光自然衔接。
        for zz,normal in ((0.,-1.),(1.,1.)):
            center=len(verts);verts.append([0,0,zz,0,0,normal,1,1,1,1,zz,.5]);base=len(verts)
            for k in range(65):
                angle=k*math.tau/64;verts.append([radius*math.cos(angle),radius*math.sin(angle),zz,0,0,normal,1,1,1,1,zz,k/64])
            for k in range(64):tri.append([center,base+k,base+k+1])
        subs.append(raw_sub(a.a,name,verts,tri));names.append(name)
    data=mesh_blob(a.a,subs,allp);put(A/'iris_fx_beam.mesh',data,'极致驱动三维光柱','3份共轴闭合圆柱，单位半径1/长度1，运行时严格缩放R9和原墙前长度')
    return {'key':'beam','source':str(CACHE/'beamvfxassets.zip'),'sha256':a.a.sha(CACHE/'beamvfxassets.zip'),'materials':names,'min':[-1,-1,0],'max':[1,1,1],'center':[0,0,.5],'bound_radius':1.118033988749895,'external_CC0':True,'limitations':'外部授权纹理适配；不冒称原驱动拥有beam.nif'}, {'duration':1.333333333,'samples':41,'peak_radius':1.5,'tracks':[{'mesh':n,'frames':[IDENT[:] for _ in range(41)]} for n in names],'cylinder_normalization':{'target_radius':1,'target_z':[0,1]}}

def mount(a):
    source=a.S/'Meshes/SW/Iris/EXanim1.nif';parts=read_parts(source);times=np.linspace(0,END,166);subs=[];names=[];tracks=[];bounds=[];materials=[];proof=[]
    # 同一原准星标尺整体变换，保留红/蓝全部源顶点相对位置；不为每个部件各造一套比例。
    cap=next(p for p in parts if p['name'].startswith('TwinChakrams:62'));raw=np.asarray(cap['vertices']);center=np.array([(raw[:,0].max()+raw[:,0].min())/2,raw[:,1].max(),(raw[:,2].max()+raw[:,2].min())/2])
    center=a.a.C@center*a.a.SCALE;frame=np.eye(4);frame[:3,3]=MU-center
    for index,p in enumerate(parts):
        points=np.asarray(p['vertices'])@a.a.C.T*a.a.SCALE+frame[:3,3];normal=np.asarray(p['normals'])@a.a.C.T;normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-9)
        name='IrisArsenal/Drive059/'+('Reticle'+p['bone'] if p['name'].startswith('Ch0145') else 'Cannon'+str(index));halo=True # 原003红形体与004蓝形体均为发光准星；不能误当实体炮片。
        texture=a.texture(p['textures'][0]);a.MATS[name]={'drive059_surface':True,'halo':halo,'diffuse':texture,'bone':p['bone'],'source_shape':p['name'],'source_shader':p['shader_data'],'blend':'src_alpha one_minus_src_alpha'};materials.append('material '+name+'\n{ technique { pass {\n lighting off\n depth_check on\n depth_write '+'on'+'\n cull_hardware none\n scene_blend '+'src_alpha one_minus_src_alpha'+'\n vertex_program_ref IrisDriveMountVP {}\n fragment_program_ref IrisDriveMountFP { param_named surface float4 '+' '.join(str(float(x)) for x in p['shader_data']['emissive']+[p['shader_data']['emissive_mult']])+'\n param_named_auto clock custom 1\n param_named_auto colour custom 2\n }\n texture_unit { texture '+texture+' }\n } } }\n')
        states=[]
        # 前段旋转频率来自EXanim.nif的NiTransformController(5Hz)/4.125秒一圈；
        # 扩张起止按已解码视频158.0～159.5的相对角色轮廓，明确是Kenshi时序适配，非虚构NIF缩放键。
        for t in times:
            state=IDENT[:];alpha=min(1,max(0,(t-.30)/.08))*min(1,max(0,(4.52-t)/.12));mat=np.eye(4)
            if halo:
                grow=np.clip((t-1.55)/1.3,0,1);grow=grow*grow*(3-2*grow);scale=.42+.58*grow
                angle=-(max(0,min(t,2.)-.30))*5*math.tau/4.125;co,si=math.cos(angle),math.sin(angle)
                # 原红/蓝两个独立顶点组保留；仅把它们共有的轴心挂到枪口，不把准星改成球体。
                localcenter=MU+np.array([0,0,-2.0]);mat[:3,:3]=np.array([[co,-si,0],[si,co,0],[0,0,1]])*scale;mat[:3,3]=localcenter-mat[:3,:3]@localcenter
            state[3]=alpha;state[13:]=mat[:3].reshape(-1).tolist();states.append(state)
            if alpha>.001:
                posed=points@mat[:3,:3].T+mat[:3,3];bounds.extend([posed.min(0),posed.max(0)])
        vertices=np.column_stack([points,normal,np.ones((len(points),4)),np.asarray(p['uv'])]);subs.append(raw_sub(a.a,name,vertices,p['triangles']));names.append(name);tracks.append({'mesh':p['name'],'frames':states});proof.append({'shape':p['name'],'vertices':len(points),'bone':p['bone'],'source_all_weights_one':True,'role':'reticle_blue' if p['name'].startswith('Ch0145') else 'reticle_red'})
    # 真正StokesCannon链的ShoutAreaExplosionSmall01：读取原网格/颜色/UV/发射器，统一缩放到枪口。
    blue=CACHE/'ShoutAreaExplosionSmall01.nif';meshes,_=a.a.read_nif(blue);meshes=[p for p in meshes if not fire_optics.refractive(p)];bd=timeline(blue,meshes,'SpecialIdle_AreaEffect',a.a.C,a.a.SCALE)
    visible=[]
    for p,tr in zip(meshes,bd['tracks']):
        points=(np.asarray(p['vertices'])@p['matrix'][:3,:3].T+p['matrix'][:3,3])@a.a.C.T*a.a.SCALE
        for t in np.linspace(0,2.24,68):
            st=sample(tr['frames'],t,bd['duration']);mat=np.asarray(st[13:]).reshape(3,4)
            if st[3]>.02:visible.extend(points@mat[:,:3].T+mat[:,3])
    peak=max(1,float(np.linalg.norm(np.asarray(visible),axis=1).max()));blueScale=22/peak;B=np.eye(4);B[:3,:3]*=blueScale;B[:3,3]=MU
    blocks={p['index']:p for p in a.nr.parse(blue)['parsed_blocks']};newmat=set(a.MATS)
    for p,tr in zip(meshes,bd['tracks']):
        blob,mats,points=a.mesh_bytes([p],blocks);oldname=mats[0];name='IrisArsenal/Drive059/Blue/'+oldname.rsplit('/',1)[-1];d=copy.deepcopy(a.MATS[oldname]);d['ion_blue']=True;a.MATS[name]=d;materials.append(shader_material(name,d))
        rows=np.array(buffers_from_bytes(blob)[0][1],copy=True);rows[:,:3]=rows[:,:3]*blueScale+MU;states=[]
        for t in times:
            state=sample(tr['frames'],max(0,t-FIRE)*4,bd['duration']);state=transform_state(state,B)
            if not FIRE<=t<BLUE_END:state[3]=0
            states.append(state)
        subs.append(raw_sub(a.a,name,rows,p['triangles']));names.append(name);tracks.append({'mesh':p['name'],'frames':states});bounds.extend(rows[:,:3])
    layers,particle_meta=drill_particles.export(a,blue,0,capacity_limit=512)
    for l in layers:
        oldname=l['material'];name='IrisArsenal/Drive059/BlueParticles/'+oldname.rsplit('/',1)[-1];l=copy.deepcopy(l);l['material']=name;params=copy.deepcopy(a.MATS[oldname]);params['ion_blue']=True;a.MATS[name]=params
        scale=particle_meta['source_peak']*blueScale
        l['particles']=[q for q in l['particles'] if q[6]<2.24]
        for q in l['particles']:
            q[:3]=(np.asarray(q[:3])*scale+MU).tolist();q[3:6]=(np.asarray(q[3:6])*scale*4).tolist();q[7]=min(q[7],2.24-q[6])/4;q[6]=FIRE+q[6]/4;q[8]*=scale
        params['acceleration']=(np.asarray(params.get('acceleration',[0,0,0]))*scale*16).tolist();materials.append(drill_particles.material(name,params,a.TEXTURES));blob,pts=drill_particles.submesh(a,l);subs.append(blob);names.append(name);tracks.append({'mesh':l['name'],'frames':[IDENT[:] for _ in times]});bounds.extend(pts)
    # 原FireWave八层作为枪口火焰，源顺序/纹理/图集/粒子位置保持；0.56秒蓝相后才点火。
    fire_states,fire_duration,_=curves(A/'effect_curves.csv','full_blast');fire_buffers=buffers(A/'iris_fx_full_blast.mesh');fire_meta=json.loads((ROOT/'docs/eight-effects.json').read_text('utf8'))['materials'];F=np.eye(4);F[:3,:3]*=18;F[:3,3]=MU
    for index,(name,raw) in enumerate(fire_buffers):
        rows=np.array(raw,copy=True);rows[:,:3]=rows[:,:3]*18+MU;particle=fire_meta[name].get('burst_particle');states=[]
        if particle:
            # 缩放18/时间4倍时，速度×72、加速度×288；专用材质保持其他九招的原重力不变。
            oldname=name;name='IrisArsenal/Drive059/FireParticles/'+str(index);params=copy.deepcopy(fire_meta[oldname]);params['acceleration']=(np.asarray(params.get('acceleration',[0,0,0]))*288).tolist();a.MATS[name]=params;materials.append(drill_particles.material(name,params,a.TEXTURES))
        if particle:
            rows[:,3:6]*=72;rows[:,6]=BLUE_END+rows[:,6]/4;rows[:,7]/=4;rows[:,8]*=18
        for t in times:
            state=IDENT[:] if particle else transform_state(sample(fire_states[index],max(0,t-BLUE_END)*4,fire_duration),F)
            if not BLUE_END<=t<END:state[3]=0
            states.append(state)
        # 索引从实际Ogre网格读取，不能根据顶点数假定三角拓扑。
        from scene_geometry import mesh
        triangles=mesh(A/'iris_fx_full_blast.mesh')[index]['tri'];subs.append(raw_sub(a.a,name,rows,triangles));names.append(name);tracks.append({'mesh':'source_fire_'+str(index),'frames':states});bounds.extend(rows[:,:3])
    # 同时覆盖所有曲线样本与真实粒子全寿命。GPU会先进行视锥裁剪，不能只包静止顶点，
    # 也不能用枪口35的猜测AABB吞掉蓝光扩散/火焰尾部；只存每层极值，避免作者内存爆涨。
    points=np.asarray(bounds);probe=mesh_blob(a.a,subs,points);dynamic=[];peak=0.
    for (_,rows),tr in zip(buffers_from_bytes(probe),tracks):
        for state in tr['frames']:
            mat=np.asarray(state[13:]).reshape(3,4);q=rows[:,:3]@mat[:,:3].T+mat[:,3];dynamic.extend([q.min(0),q.max(0)]);peak=max(peak,float(np.linalg.norm(q,axis=1).max()))
    for name,rows in buffers_from_bytes(probe):
        params=a.MATS.get(name,fire_meta.get(name,{}))
        if not params.get('burst_particle'):continue
        for q in rows[::4]:
            life=q[7];acc=np.asarray(params.get('acceleration',[0,0,0]));extent=q[8]*max(params['size_curve'])*math.sqrt(2)
            for age in np.linspace(0,life,17):
                center=q[:3]+q[3:6]*age+.5*acc*age*age;dynamic.extend([center-extent,center+extent]);peak=max(peak,float(np.linalg.norm(abs(center)+extent)))
    points=np.concatenate([points,np.asarray(dynamic)]);data=mesh_blob(a.a,subs,points);put(A/'iris_fx_ion.mesh',data,'极致驱动源附件/准星/枪口阶段','EXanim1九组原红准星/原蓝两组、真实ShoutSmall蓝粒子与原FireWave八层；独立于其他九招')
    static=np.concatenate([v[:,:3] for _,v in buffers_from_bytes(data)]);static_center=(static.min(0)+static.max(0))*.5
    return {'key':'ion','source':str(source),'sha256':a.a.sha(source),'materials':names,'min':static.min(0).tolist(),'max':static.max(0).tolist(),'center':static_center.tolist(),'bound_radius':float(np.linalg.norm(static-static_center,axis=1).max()),'drive059_source_parts':proof,'limitations':'源红蓝准星刚性组精确读取；握点/准星缩放/相位为Kenshi适配。未模拟Skyrim全部拖曳/折射/行为图'}, {'duration':END,'samples':len(times),'peak_radius':peak,'tracks':tracks},materials,{'blue_source':str(blue),'blue_sha256':a.a.sha(blue),'blue_scale':blueScale,'blue_phase':[FIRE,BLUE_END],'fire_phase':[BLUE_END,END],'blue_radius':22,'fire_radius':18,'fire_source':'IrisExplosion / 0x3f9ed FireWave -> VoiceFlameWaveProject03.nif / existing full_blast','muzzle_local':MU.tolist(),'source_cannon_cap':center.tolist(),'parts':proof,'particle_translation':particle_meta}

def buffers_from_bytes(blob):
    # 使用既有严格布局读取器的同一格式，只读内存字节，不写临时网格。
    import struct
    from scene_geometry import chunks
    out=[]
    for kind,s,e in chunks(blob,blob.index(b'\n')+1,len(blob)):
        if kind!=0x3000:continue
        for kind,ss,ee in chunks(blob,s+1,e):
            if kind!=0x4000:continue
            nl=blob.index(b'\n',ss);name=blob[ss:nl].decode();shared,n,wide=struct.unpack_from('<?I?',blob,nl+1);offset=nl+7+n*(4 if wide else 2)
            for typ,start,end in chunks(blob,offset,ee):
                if typ!=0x5000:continue
                count=struct.unpack_from('<I',blob,start)[0]
                for typ,x,y in chunks(blob,start+4,end):
                    if typ==0x5200:
                        bind,stride=struct.unpack_from('<HH',blob,x);assert stride==48
                        for typ,u,z in chunks(blob,x+4,y):
                            if typ==0x5210:out.append((name,np.frombuffer(blob[u:z],'<f4').reshape(count,12)))
    return out

def apply(a):
    original_materials=copy.deepcopy(a.MATS) # 后处理的专用元数据不能污染同进程下一次原九招重建。
    beam_asset,beam_curve=beam(a);ion_asset,ion_curve,materials,record=mount(a)
    # 新程序/材质独立文件，其他九招的原shader和原材质块不改；更新只替换beam/ion两行合同。
    from drive_shader059 import SHADER,PROGRAM,stream_materials
    put(A/'iris_drive059.hlsl',SHADER,'极致驱动专用Shader源码','CC0双纹理/三同轴层流动；原炮体和红蓝纹理专用读取，不编译')
    put(A/'iris_drive059.program',PROGRAM,'极致驱动专用GPU声明','vs_4_0/ps_4_0与现Ogre资源加载一致；参数由自有实例传递')
    put(A/'iris_drive059.material',stream_materials()+'\n'.join(materials),'极致驱动专用材质','与其他九招隔离；游戏时钟流动，原源贴图和CC0许可保留')
    for name,data in a.TEXTURES.items():put(A/name,data,'实际源贴图','只补真实源蓝光/炮体贴图；已存在同字节文件保持')
    lines=(A/'effects.csv').read_text('utf8').splitlines();out=[lines[0]];i=1
    while i<len(lines):
        row=lines[i].split();count=int(row[2]);i+=1;names=lines[i:i+count];i+=count;replacement={'beam':beam_asset,'ion':ion_asset}.get(row[0])
        if replacement:
            names=replacement['materials'];row=[replacement['key'],'iris_fx_'+replacement['key']+'.mesh',str(len(names))]+['%.9f'%v for v in replacement['center']+[replacement['bound_radius']]]
        out.append(' '.join(row));out.extend(names)
    put(A/'effects.csv','\n'.join(out)+'\n','运行时子网格合同','只更新驱动beam/ion两项；数目与原网格完全匹配')
    lines=(A/'effect_curves.csv').read_text('utf8').splitlines();out=[];i=1;kept=0
    while i<len(lines):
        row=lines[i].split();count=int(row[1])*int(row[2]);block=lines[i:i+1+count];i+=1+count
        if row[0] in ('beam','ion'):continue
        out.extend(block);kept+=1
    for key,d in [('beam',beam_curve),('ion',ion_curve)]:
        out.append('%s %d %d %.9f %.9f'%(key,len(d['tracks']),d['samples'],d['duration'],d['peak_radius']))
        for tr in d['tracks']:out.extend(' '.join('%.9f'%float(v) for v in state) for state in tr['frames'])
    put(A/'effect_curves.csv','IRIS_FX_CURVES 1 '+str(kept+2)+'\n'+'\n'.join(out)+'\n','驱动完整层时钟','其他效果原曲线逐行保持；驱动附件使用PA10局部时钟、蓝火分期和四脉冲连续光流')
    doc=json.loads((ROOT/'docs/eight-effects.json').read_text('utf8'))
    for replacement,curve in [(beam_asset,beam_curve),(ion_asset,ion_curve)]:
        doc['assets']=[replacement if x['key']==replacement['key'] else x for x in doc['assets']];doc['timelines'][replacement['key']]={k:v for k,v in curve.items() if k!='tracks'}
    doc['drive059']={**record,'beam':'CC0 BeamVFXAssets; true R9 flat cylinder; original length unchanged','reference_video_seconds':[157,162],'original_drive_chain':'PA10 IrisEXAnimSHOOT -> StokesCannon scripted impact / FireWave; original not a beam','reticle':'actual EXanim1 Ch0145_Halo 180 vertices / AnimObjectA,B; source rotation frequency5/4.125; video-constrained growth adaptation'}
    doc['materials'].update({k:v for k,v in a.MATS.items() if k not in doc['materials'] and k in {n for asset in doc['assets'] for n in asset['materials']}});doc['textures']=a.canonical_provenance(a.PROVENANCE,a.MATS)
    put(ROOT/'docs/eight-effects.json',json.dumps(doc,ensure_ascii=False,indent=2),'驱动来源与适配证据','更新驱动两种资产和来源/限制，不改其他招式的源记录')
    put(ROOT/'docs/drive059-assets.json',json.dumps(doc['drive059'],ensure_ascii=False,indent=2),'059源资源证据','实际炮体/准星骨权、蓝光源链/时序、CC0外部光流及校准坐标')

    a.MATS.clear();a.MATS.update(original_materials)
