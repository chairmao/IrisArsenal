"""040按FullBust_End/PROJ.NAM1真实引用展开火焰，禁止随机改摆成若干小火团。"""
import copy,itertools,json,struct
import numpy as np
from safeio import ROOT,put
from fx_timeline import timeline,raw_blocks
from nif_reader import parse,Reader
import drill_particles,fire_optics

IDENTITY=[1,1,1,1,0,0,1,1,1,1,0,1,1,1,0,0,0,0,1,0,0,0,0,1,0]

def nodes(path):
    raw,strings=raw_blocks(path);out={}
    for index,(kind,data) in raw.items():
        if kind not in ('BSFadeNode','NiNode','BSValueNode','BSTriShape'):continue
        r=Reader(data);name,ctl,m=drill_particles.av(r,strings)
        children=[r.read('i') for _ in range(r.read('I'))] if kind!='BSTriShape' else []
        out[index]={'name':name,'matrix':m,'parent':-1,'children':children}
        if kind=='BSValueNode':
            assert r.read('I')==0 # 源NiNode的effects为空；接下来才是附加节点ID。
            out[index]['addon']=r.read('I');out[index]['flags']=r.read('B');r.done()
    for index,n in out.items():
        for c in n['children']:
            if c in out:out[c]['parent']=index
    def world(i):
        n=out[i];return n['matrix'] if n['parent']<0 else world(n['parent'])@n['matrix']
    for i,n in out.items():n['world']=world(i)
    return out

def curve_sample(frames,t,duration):
    old=np.asarray(frames);x=np.clip(t/duration,0,1)*(len(old)-1);lo=int(x);hi=min(len(old)-1,lo+1)
    return old[lo]*(1-(x-lo))+old[hi]*(x-lo)

def part_bounds(layers):
    out=[]
    for l in layers:
        for q in l['particles']:
            half=q[8]*max(l['size_curve'])*np.sqrt(2)
            acc=np.asarray(l.get('acceleration',[0,0,0]));v=np.asarray(q[3:6]);times=[0,q[7]]
            times.extend(-v[k]/acc[k] for k in range(3) if abs(acc[k])>1e-12 and 0<-v[k]/acc[k]<q[7])
            for t in times:
                p=np.asarray(q[:3])+v*t+.5*acc*t*t
                out.extend(p+np.asarray(sign)*half for sign in itertools.product((-1,1),repeat=3))
    return np.asarray(out)

def pack(a,source,meshes,tracks,layers,duration,record,start=0,profile=None):
    """主网格与所有附加发射体用同一个尺度；绝不逐层归一/反射/散布。"""
    all_points=[];bounds=[];culling=[]
    for mesh,tr in zip(meshes,tracks):
        p=(np.asarray(mesh['vertices'])@mesh['matrix'][:3,:3].T+mesh['matrix'][:3,3])@a.a.C.T*a.a.SCALE;all_points.append(p)
        for s in tr['frames']:
            m=np.asarray(s[13:]).reshape(3,4);q=p@m[:,:3].T+m[:,3];culling.extend(q)
            if s[3]<.001 or max(s[:3])*s[8]<.001:continue
            bounds.extend(q)
    if layers:bounds.extend(part_bounds(layers))
    bounds=np.asarray(bounds);peak=float(np.linalg.norm(bounds,axis=1).max());assert peak>0
    # 两招旧范围与新R90都要求统一缩放；只对整份源效果作一次相似变换，不重排源空间关系。
    for mesh,tr in zip(meshes,tracks):
        mesh['matrix'][:3]/=peak
        for s in tr['frames']:
            for k in (16,20,24):s[k]/=peak
    for l in layers:
        l['acceleration']=(np.asarray(l.get('acceleration',[0,0,0]))/peak).tolist();a.MATS[l['material']]['acceleration']=l['acceleration']
        for q in l['particles']:
            for k in range(6):q[k]/=peak
            q[8]/=peak;q[6]+=start
    display_scale=1.
    if profile:
        from fire_coverage import calibrate
        display_scale,calibration=calibrate(a,layers,tracks,duration,start,profile);record['coverage_calibration']=calibration
        # 主体alpha轮廓决定显示比例，原保守包围仍只管裁剪；全体同一相似变换，不重排火焰。
        for mesh,tr in zip(meshes,tracks):
            mesh['matrix'][:3]*=display_scale
            for state in tr['frames']:
                for k in (16,20,24):state[k]*=display_scale
        for layer in layers:
            previous=layer['material'];name=previous+('/Coverage042/' if profile=='full' else '/Coverage041/')+profile
            if name not in a.MATS:a.MATS[name]=copy.deepcopy(a.MATS[previous])
            layer['material']=name;layer['acceleration']=(np.asarray(layer['acceleration'])*display_scale).tolist();a.MATS[name]['acceleration']=layer['acceleration']
            for p in layer['particles']:
                for k in range(6):p[k]*=display_scale
                p[8]*=display_scale
    end=duration+start;samples=round(end*30)+1;assert 0<end<=8 and samples<=241
    subs=[];points=[];names=[];outtracks=[]
    blocks={b['index']:b for b in parse(source)['parsed_blocks']}
    for mesh,tr in zip(meshes,tracks):
        # Wisps03:0没有纹理，完全靠源顶点alpha羽化；保留原绑定，不再借别的光斑伪装成火焰。
        raw,mats,p=a.mesh_bytes([mesh],blocks);offset=raw.index(b'\n')+8;kind,length=struct.unpack_from('<HI',raw,offset);assert kind==0x4000
        frames=[]
        for t in np.linspace(0,end,samples):
            s=curve_sample(tr['frames'],t-start,duration)
            if t<start or t>=end:s[3]=0
            frames.append(s.tolist())
        subs.append(raw[offset:offset+length]);points.append(p);names.extend(mats);outtracks.append({'mesh':mesh['name'],'frames':frames})
    # 原MasterParticleSystem只有两份渲染系统，七处是发射对象；按同材质/同重力合批保持原结构。
    # 每粒的出生位置、速度、寿命和角度仍独立，不能增加14份绘制来模拟同一个原粒子池。
    grouped={}
    for layer in layers:
        name=layer['material']
        if name not in grouped:
            grouped[name]=copy.deepcopy(layer);grouped[name]['particles']=[];grouped[name]['source_nodes']=[]
        grouped[name]['particles'].extend(copy.deepcopy(layer['particles']));grouped[name]['source_nodes'].append(layer.get('addon_node'))
    render_layers=list(grouped.values());record['render_layers']=render_layers
    for l in render_layers:
        sub,p=drill_particles.submesh(a,l);subs.append(sub);points.append(p);names.append(l['material']);outtracks.append({'mesh':l['name'],'frames':[IDENTITY[:] for _ in range(samples)]})
    points=np.concatenate(points);bounds=bounds/peak*display_scale;bounds=np.concatenate([bounds,np.asarray(culling)/peak*display_scale if culling else points,part_bounds(layers),points])
    record.update({'source':str(source),'sha256':a.a.sha(source),'source_peak':peak/display_scale,'start':start,'life':end,'layers':layers,'bounds':bounds.tolist(),'geometry':{'shapes':[{'name':m['name'],'vertices':len(m['vertices']),'rank':int(np.linalg.matrix_rank(np.asarray(m['vertices'])-np.asarray(m['vertices']).mean(0)))} for m in meshes]},'adaptation':'源曲面/源7个附加节点位置与出生姿态/源MPS容量发射率和纹理；整体单一尺度，未重排、未八象限反射；读取原初始角度与匀强重力；未执行Skyrim屏幕折射、BSLagBone、受控力/拖曳/湍流/非零随机角速度'})
    return {'source':source,'record':record,'subs':subs,'points':points,'materials':names,'bounds':bounds,'duration':end,'samples':samples,'tracks':outtracks}

def components(a,start,profile=None):
    source=ROOT/'tools/source-cache/VoiceFlameWaveProject03.nif';child=ROOT/'tools/source-cache/MPSFireWaveFlames.nif'
    meshes,_=a.a.read_nif(source);meshes=[copy.deepcopy(m) for m in meshes if not fire_optics.refractive(m)]
    assert [m['name'] for m in meshes]==['Trail11:1','Trail10:1','Trail09:1','Trail12:1','Wisps03:0','Wisps03:1']
    ns=nodes(source);addons=[(i,n) for i,n in ns.items() if n.get('addon')==64];assert len(addons)==7
    # 哑点只为读取原TimeHelper/Attach层级的出生矩阵，不新增可绘制面或对角色写任何变换。
    proxies=[]
    for i,n in addons:
        p=copy.deepcopy(meshes[0]);p.update({'name':n['name']+'#'+str(i),'index':i,'matrix':n['world'],'vertices':[[0,0,0]]});proxies.append(p)
    doc=timeline(source,meshes+proxies,None,a.a.C,a.a.SCALE)
    layers,base=drill_particles.export(a,child,0);assert len(layers)==2
    H=np.eye(4);H[:3,:3]=a.a.C*a.a.SCALE;Hi=np.linalg.inv(H);combined=[]
    for (i,n),tr in zip(addons,doc['tracks'][len(meshes):]):
        transform=H@n['world']@Hi
        for original in layers:
            l=copy.deepcopy(original);l['name']+='@AddOn64-'+str(i)
            # 每个原附加节点使用相同原MPS材质；共享贴图，不按层复制高分辨率纹理。
            l['addon_node']=i;l['source_world_matrix']=n['world'].tolist()
            l['acceleration']=(np.asarray(l['acceleration'])*base['source_peak']).tolist()
            for q in l['particles']:
                state=curve_sample(tr['frames'],q[6],doc['duration']);delta=np.eye(4);delta[:3]=state[13:].reshape(3,4);M=delta@transform
                p=np.asarray(q[:3])*base['source_peak'];v=np.asarray(q[3:6])*base['source_peak']
                q[:3]=(M[:3,:3]@p+M[:3,3]).tolist();q[3:6]=(M[:3,:3]@v).tolist();q[8]*=base['source_peak']*np.linalg.norm(M[:3,0])
            combined.append(l)
    # 原七个AddOn共享同一MPS池；按出生/死亡处理容量，不能误当七份独立300/210容量。
    for material in {l['material'] for l in combined}:
        candidates=sorted((q[6],i,j,q) for i,l in enumerate(combined) if l['material']==material for j,q in enumerate(l['particles']))
        active=[];keep=set();capacity=next(l['source_capacity'] for l in combined if l['material']==material)
        for birth,i,j,q in candidates:
            active=[end for end in active if end>birth]
            if len(active)>=capacity:continue
            active.append(birth+q[7]);keep.add((i,j))
        for i,l in enumerate(combined):
            if l['material']==material:l['particles']=[q for j,q in enumerate(l['particles']) if (i,j) in keep]
    record={'chain':['PIE.$FullBust_End','Skyrim.esm:SPEL 0003F9ED','MGEF 000562EB','PROJ 000647BE','Magic/VoiceFlameWaveProject03.nif','BSValueNode ID64 ×7','ADDN 000647BC','MPS/MPSFireWaveFlames.nif'],'addon_source':str(child),'addon_sha256':a.a.sha(child),'addon_count':7,'source_particle_parameters':base,'video_seconds':[109.8,112.5]}
    c=pack(a,source,meshes,doc['tracks'][:len(meshes)],combined,max(doc['duration'],base['life']),record,start,profile)
    return c

def emit_asset(a,key,c):
    p=c['points'];bounds=c['bounds'];lo=np.minimum(p.min(0),bounds.min(0));hi=np.maximum(p.max(0),bounds.max(0));peak=float(np.linalg.norm(bounds,axis=1).max())
    raw=b'\x00\x10[MeshSerializer_v1.41]\n'+a.a.chunk(0x3000,b'\0'+b''.join(c['subs'])+a.a.chunk(0x9000,struct.pack('<7f',*lo,*hi,peak)))
    put(a.A/('iris_fx_'+key+'.mesh'),raw,'原资源效果网格','完整源层级/曲面/纹理/有限附加粒子；不任意拼凑火团')
    asset={'key':key,'source':str(c['source']),'sha256':a.a.sha(c['source']),'materials':c['materials'],'min':p.min(0).tolist(),'max':p.max(0).tolist(),'center':((p.max(0)+p.min(0))*.5).tolist(),'bound_radius':float(np.linalg.norm(p-(p.max(0)+p.min(0))*.5,axis=1).max()),'particle_mesh':True,'reference_radius':1,'limitations':c['record']['adaptation']}
    curve={'duration':c['duration'],'samples':c['samples'],'peak_radius':peak,'bounds':[lo.tolist(),hi.tolist()],'tracks':c['tracks']}
    return asset,curve

def standalone(a,key='fire_blast'):
    c=components(a,0,'roll' if key=='roll_blast' else 'full' if key=='full_blast' else None);put(ROOT/('docs/fire-roll-041.json' if key=='roll_blast' else 'docs/fire-full-042.json' if key=='full_blast' else 'docs/fire-burst-040.json'),json.dumps(c['record'],ensure_ascii=False,indent=2),'原火焰引用证据','FullBust_End到原FireWave七发射点与六片曲面；不是通用火球')
    return emit_asset(a,key,c)

def muzzle(a):
    source=ROOT/'tools/source-cache/MPSFireBoltImpact01.nif';layers,record=drill_particles.export(a,source,0)
    import muzzle_detail
    record['detail042']=muzzle_detail.decorate(source,layers,a.MATS)
    moves=json.loads((ROOT/'docs/eight-moves.json').read_text('utf8'))['moves'];times=[e['time']-moves[5]['events'][0]['time'] for e in moves[5]['events']];assert len(times)==20
    wrapper=a.ELDEN/'meshes/RimMagic/SW_MagMuzzle.nif';ns=nodes(wrapper);node=next(n for n in ns.values() if n.get('addon')==9)
    proxy=copy.deepcopy(a.a.read_nif(ROOT/'tools/source-cache/VoiceFlameWaveProject03.nif')[0][0]);proxy.update(index=2,name=node['name'],matrix=node['world'],vertices=[[1,0,0]])
    parent=timeline(wrapper,[proxy],None,a.a.C,a.a.SCALE);H=np.eye(4);H[:3,:3]=a.a.C*a.a.SCALE;static=H@node['world']@np.linalg.inv(H)
    # SW_MagMuzzle本身只有AddOnNode09；发射体沿原枪口附着，不把命中爆炸或原准星当枪口火焰。
    # 原MPS是共享容量的发射池；按真实20次触发展开后，只有容量内存活粒子才能接受新的出生。
    for l in layers:
        original=copy.deepcopy(l['particles']);births=[]
        for t in times:
            for q in original:
                q=q[:];q[6]+=t
                for k in range(6):q[k]*=record['source_peak']
                q[8]*=record['source_peak']
                # 保留原0.1秒枪口旋转曲线，粒子出生后留在它自己的源运动里。
                st=curve_sample(parent['tracks'][0]['frames'],q[6]-t,parent['duration']);M=np.eye(4);M[:3]=st[13:].reshape(3,4);M=M@static
                q[:3]=(M[:3,:3]@q[:3]+M[:3,3]).tolist();q[3:6]=(M[:3,:3]@q[3:6]).tolist();births.append(q)
        active=[];accepted=[]
        for q in sorted(births,key=lambda q:q[6]):
            active=[end for end in active if end>q[6]]
            if len(active)>=l['source_capacity']:continue
            active.append(q[6]+q[7]);accepted.append(q)
        l['particles']=accepted
    for l in layers:
        l['acceleration']=(np.asarray(l['acceleration'])*record['source_peak']).tolist();a.MATS[l['material']]['acceleration']=l['acceleration']
    life=max(q[6]+q[7] for l in layers for q in l['particles']);samples=round(life*30)+1;assert life<8
    subs=[];points=[];names=[];tracks=[]
    for l in layers:
        sub,p=drill_particles.submesh(a,l);subs.append(sub);points.append(p);names.append(l['material']);tracks.append({'mesh':l['name'],'frames':[IDENTITY[:] for _ in range(samples)]})
    c={'source':source,'record':record,'subs':subs,'points':np.concatenate(points),'materials':names,'bounds':part_bounds(layers),'duration':life,'samples':samples,'tracks':tracks}
    record.update({'chain':['IrisShoot1','soulworker_iris.esp:PROJ 0400085D NAM1','RimMagic/SW_MagMuzzle.nif','BSValueNode ID9','Skyrim.esm:ADDN 0002B95B','MPS/MPSFireBoltImpact01.nif'],'trigger_times':times,'layers':layers,'adaptation':'原5层枪口火焰/火星/余烬/闪光；实际20射击点、原容量池、枪口跟随；未完整模拟NiPSys重力/拖曳'})
    put(ROOT/'docs/muzzle-fire-042.json',json.dumps(record,ensure_ascii=False,indent=2),'枪口引用/有限容量证据','原NAM1和ADDN09，和飞弹/准星资源、医疗完全分开')
    return emit_asset(a,'muzzle_fire',c)
