"""只读源NIF的刚体与光学时间曲线，导出有界采样；不运行Skyrim控制器或生成GPU二进制。"""
import math,struct
import numpy as np
from nif_reader import Reader,parse

def raw_blocks(path):
    raw=path.read_bytes();r=Reader(raw[raw.index(b'\n')+1:]);version=r.read('I');endian=r.read('B');user=r.read('I');count=r.read('I');bs=r.read('I')
    assert (version,endian,user)==(0x14020007,1,12) and bs in (83,100)
    for _ in range(3):r.string('B')
    types=[r.string() for _ in range(r.read('H'))];ix=[r.read('H') for _ in range(count)];sizes=[r.read('I') for _ in range(count)]
    ns=r.read('I');r.read('I');strings=[r.string() for _ in range(ns)]
    for _ in range(r.read('I')):r.read('I')
    out={}
    for i,(ti,size) in enumerate(zip(ix,sizes)):
        out[i]=(types[ti],r.data[r.pos:r.pos+size]);r.pos+=size
    return out,strings

def group(r,dim=1):
    n=r.read('I');kind=r.read('I') if n else 0;assert n<=4096 and kind in (0,1,2,3,5)
    keys=[]
    for _ in range(n):
        k={'time':r.read('f'),'value':r.read(str(dim)+'f')}
        if kind==2:k['forward']=r.read(str(dim)+'f');k['backward']=r.read(str(dim)+'f')
        if kind==3:k['tbc']=r.read('3f')
        keys.append(k)
    return {'interpolation':kind,'keys':keys}

def sample(data,t,default):
    ks=data.get('keys',[])
    if not ks:return np.asarray(default,dtype=float)
    if t<=ks[0]['time']:return np.asarray(ks[0]['value'],float)
    if t>=ks[-1]['time']:return np.asarray(ks[-1]['value'],float)
    i=next(i for i in range(len(ks)-1) if ks[i]['time']<=t<ks[i+1]['time']);a,b=ks[i:i+2];u=(t-a['time'])/(b['time']-a['time'])
    x,y=np.asarray(a['value'],float),np.asarray(b['value'],float)
    if data.get('interpolation')==5:return x
    if data.get('interpolation')==3:
        def tangent(j,outgoing):
            v=ks[j];before=ks[max(0,j-1)];after=ks[min(len(ks)-1,j+1)];T,B,C=v['tbc'];left=(np.asarray(v['value'])-np.asarray(before['value']))/max(1e-9,v['time']-before['time']);right=(np.asarray(after['value'])-np.asarray(v['value']))/max(1e-9,after['time']-v['time'])
            if j==0:left=right
            if j==len(ks)-1:right=left
            c=C if outgoing else -C
            return .5*(1-T)*((1+c)*(1+B)*left+(1-c)*(1-B)*right)
        dt=b['time']-a['time'];return (2*u**3-3*u*u+1)*x+(u**3-2*u*u+u)*tangent(i,True)*dt+(-2*u**3+3*u*u)*y+(u**3-u*u)*tangent(i+1,False)*dt
    if data.get('interpolation')==2:return (2*u**3-3*u*u+1)*x+(u**3-2*u*u+u)*np.asarray(a['forward'])+(-2*u**3+3*u*u)*y+(u**3-u*u)*np.asarray(b['backward'])
    return x*(1-u)+y*u

def rotation(q):
    w,x,y,z=q;n=np.linalg.norm(q)
    if not np.isfinite(n) or n<1e-8:return np.eye(3)
    w,x,y,z=np.asarray(q)/n
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])

def timeline(path,meshes,sequence_name,axis,scale,loop_transforms=False):
    """网格已烘焙默认世界矩阵；输出H*W(t)*W(0)^-1*H^-1，只作用自有网格顶点。"""
    parsed=parse(path);blocks={b['index']:dict(b) for b in parsed['parsed_blocks']};raw,strings=raw_blocks(path);nodes={};transforms={};interpolators={}
    for i,(kind,data) in raw.items():
        r=Reader(data)
        if kind in ('BSFadeNode','NiNode','NiBillboardNode','BSTriShape','NiTriShape','BSValueNode'):
            name=r.read('I');extra=[r.read('i') for _ in range(r.read('I'))];controller=r.read('i');r.read('I');pos=r.read('3f');rot=r.read('9f');s=r.read('f');r.read('i')
            matrix=np.eye(4);matrix[:3,:3]=np.asarray(rot).reshape(3,3)*s;matrix[:3,3]=pos
            children=[r.read('i') for _ in range(r.read('I'))] if kind not in ('BSTriShape','NiTriShape') else []
            nodes[i]={'name':strings[name] if name!=0xffffffff else '', 'matrix':matrix,'children':children,'parent':-1}
        elif kind=='NiBoolInterpolator':
            blocks[i]={'constant':r.read('B'),'data':r.read('i')};r.done()
        elif kind=='NiVisController':
            b={'next':r.read('i'),'flags':r.read('H'),'frequency':r.read('f'),'phase':r.read('f'),'start':r.read('f'),'stop':r.read('f'),'target':r.read('i'),'interpolator':r.read('i')};r.done();blocks[i]=b
        elif kind=='NiTransformController':
            # 火焰吐息是自带时钟的控制器链，没有NiControllerSequence；严格读取同一NiTimeController布局。
            blocks[i]={'type':kind,'next':r.read('i'),'flags':r.read('H'),'frequency':r.read('f'),'phase':r.read('f'),'start':r.read('f'),'stop':r.read('f'),'target':r.read('i'),'interpolator':r.read('i')};r.done()
        elif kind=='NiTransformInterpolator':
            interpolators[i]={'position':r.read('3f'),'rotation':r.read('4f'),'scale':r.read('f'),'data':r.read('i')};r.done()
        elif kind=='NiTransformData':
            nr=r.read('I');typ=r.read('I') if nr else 0;d={'rotation_type':typ,'rotation':[],'xyz':[]}
            if nr and typ==4:d['xyz']=[group(r) for _ in range(3)]
            elif nr:
                assert typ in (1,2),'未知四元数插值'
                d['rotation']=[{'time':r.read('f'),'value':r.read('4f')} for _ in range(nr)]
            d['position']=group(r,3);d['scale']=group(r);r.done();transforms[i]=d
    for i,node in nodes.items():
        for child in node['children']:
            if child in nodes:nodes[child]['parent']=i
    if sequence_name is None:
        # 只消费文件实际存在的目标/插值器/时间；不造一套随机爆炸曲线。源其他序列路径保持原样。
        controlled=[]
        for index,b in blocks.items():
            kind=b.get('type','');target=b.get('target',-1)
            if kind=='NiTransformController' and target in nodes:
                controlled.append({'node':nodes[target]['name'],'controller_type':kind,'controller':index,'interpolator':b['interpolator']})
            elif kind.startswith('BSEffectShaderProperty') and 'Controller' in kind:
                controlled.append({'node':'@shader'+str(target),'property':'BSEffectShaderProperty','controller_type':kind,'controller':index,'interpolator':b['interpolator']})
        assert controlled
        seq={'controlled_blocks':controlled,'start':0,'stop':max(b['stop'] for b in blocks.values() if b.get('type')=='NiTransformController')}
    else:
        seq=next(b for b in blocks.values() if b.get('type')=='NiControllerSequence' and b['name']==sequence_name)
    controllers={}
    for c in seq['controlled_blocks']:
        controllers.setdefault(c['node'],[]).append(c)
        if c['controller'] in blocks:blocks[c['controller']]['interpolator']=c['interpolator']
    length=seq['stop']-seq['start'];assert 0<length<=8
    count=round(length*30)+1;times=np.linspace(seq['start'],seq['stop'],count);H=np.eye(4);H[:3,:3]=np.asarray(axis)*scale;Hi=np.linalg.inv(H)
    def world(i,t):
        node=nodes[i];local=node['matrix'].copy()
        for c in controllers.get(node['name'],[]):
            if c['controller_type']!='NiTransformController':continue
            ip=interpolators.get(c['interpolator'])
            if ip is None:continue
            st=t
            if c['controller'] in raw:
                cr=Reader(raw[c['controller']][1]);cr.read('i');flags=cr.read('H');frequency=cr.read('f');phase=cr.read('f');st=t*frequency+phase
                # 063仅火神源准星启用：按NiTimeController的loop/reverse/clamp位在源区间取样。
                # 其他招式默认False逐字保留旧结果；不能让5倍时钟控制器过首圈后夹在2π静止。
                if loop_transforms:
                    begin,end=cr.read('2f');span=end-begin;cycle=(flags>>1)&3
                    if span>0 and cycle==0:st=begin+(st-begin)%span
                    elif span>0 and cycle==1:
                        x=(st-begin)%(2*span);st=begin+(x if x<=span else 2*span-x)
                    elif span>0:st=max(begin,min(end,st))
            d=transforms.get(ip['data'],{});pos=sample(d.get('position',{}),st,ip['position']);s=float(sample(d.get('scale',{}),st,ip['scale']))
            # NIF的无效常量为负FLT_MAX；缺轨道时沿用静止矩阵，不能把哨兵写入GPU。
            if not np.isfinite(pos).all() or max(abs(pos))>1e6:pos=local[:3,3]
            if not math.isfinite(s) or abs(s)>1e6:s=float(np.linalg.norm(local[:3,0]))
            if d.get('xyz'):
                x,y,z=[float(sample(v,st,0)) for v in d['xyz']];cx,sx,cy,sy,cz,sz=math.cos(x),math.sin(x),math.cos(y),math.sin(y),math.cos(z),math.sin(z)
                R=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])@np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])@np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
            elif d.get('rotation'):
                ks=d['rotation'];q=sample({'keys':ks,'interpolation':1},st,ip['rotation']);R=rotation(q)
            elif max(abs(np.asarray(ip['rotation'])))<1e6:R=rotation(ip['rotation'])
            else:R=local[:3,:3]/max(1e-9,np.linalg.norm(local[:3,0]))
            local[:3,:3]=R*s;local[:3,3]=pos
        return local if node['parent']<0 else world(node['parent'],t)@local
    tracks=[];all_points=[]
    for mesh in meshes:
        sh=mesh['shader_data'];fx=sh.get('effect');frames=[];W0=mesh['matrix'];shader=mesh['shader'];name=mesh['name']
        base_col=fx['base_color'] if fx else list(sh['emissive'])+[sh['alpha']];base_gain=fx['base_color_scale'] if fx else 1
        for t in times:
            col=list(base_col);uv=list(sh['uv_offset'])+list(sh['uv_scale']);gain=base_gain;visibility=1;fall=list(fx['falloff']) if fx else [1,0,1,1]
            active=list(controllers.get(name,[]));ni=mesh['index']
            while ni>=0:
                for vc in controllers.get(nodes[ni]['name'],[]):
                    if vc['controller_type']=='NiVisController' and vc not in active:active.append(vc)
                ni=nodes[ni]['parent']
            for cs in controllers.values():
                for c in cs:
                    if blocks.get(c['controller'],{}).get('target')==shader and c not in active:active.append(c)
            for c in active:
                ct=c['controller_type'];b=blocks.get(c['controller'],{});ip=blocks.get(c['interpolator'],{});d=blocks.get(ip.get('data'),{});st=t*b.get('frequency',1)+b.get('phase',0)
                # 自运行火浪UV控制器有源loop位；只在此新增路径按自身周期循环，源alpha/clamp不重播。
                if sequence_name is None and b.get('flags',0)&6==0 and b.get('stop',0)>b.get('start',0):
                    st=b['start']+(st-b['start'])%(b['stop']-b['start'])
                if ct=='NiVisController' and d.get('keys'):visibility=next((k['value'] for k in reversed(d['keys']) if k['time']<=st),d['keys'][0]['value'])
                if c.get('property')!='BSEffectShaderProperty':continue
                value=sample(d,st,ip.get('constant',0));variable=b.get('variable')
                if 'ColorController' in ct and np.asarray(value).size==3 and variable==0:col[:3]=np.asarray(value).tolist()
                if 'FloatController' in ct:
                    value=float(value)
                    if variable==0:gain=value
                    elif variable in (1,2,3,4):fall[variable-1]=value
                    elif variable==5:col[3]=value
                    elif variable in (6,7,8,9):uv[{6:0,7:2,8:1,9:3}[variable]]=value
            col[3]=max(0,min(1,col[3]))*visibility
            delta=H@world(mesh['index'],t)@np.linalg.inv(W0)@Hi
            state=col+uv+[gain]+fall+delta[:3,:].reshape(-1).tolist();assert len(state)==25 and np.isfinite(state).all() and max(abs(np.asarray(state)))<1e6
            frames.append(state)
            p=(np.asarray(mesh['vertices'])@W0[:3,:3].T+W0[:3,3])@np.asarray(axis).T*scale
            all_points.append(p@delta[:3,:3].T+delta[:3,3])
        tracks.append({'mesh':name,'frames':frames})
    points=np.concatenate(all_points);peak=float(np.linalg.norm(points,axis=1).max());assert peak>0
    return {'sequence':sequence_name,'duration':float(length),'samples':count,'tracks':tracks,'peak_radius':peak,'bounds':[points.min(0).tolist(),points.max(0).tolist()], 'source_sha256':parsed['sha256']}
