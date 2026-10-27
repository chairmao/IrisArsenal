"""原ALS电火花与SW_FireExplosion有限发射器离线翻译；不借用地震喷流，不创建物理体。"""
import math,struct,itertools
import numpy as np
from nif_reader import Reader,parse
from fx_timeline import raw_blocks,sample

def av(r,strings):
    name=strings[r.read('I')];[r.read('i') for _ in range(r.read('I'))];ctl=r.read('i');r.read('I')
    p=r.read('3f');rot=r.read('9f');s=r.read('f');r.read('i');m=np.eye(4);m[:3,:3]=np.asarray(rot).reshape(3,3)*s;m[:3,3]=p
    return name,ctl,m

def atlas_layout(data):
    # 按完整NiPSys矩形表验证列/行/帧数；不能把2048x1024的8x4图集猜成正方形或整张火球贴图。
    # 只接受逐格行优先的规则图集，匹配所有UV矩形，避免把别的整数/浮点误当frame count。
    found=[]
    for count in (4,8,16,32,64):
        token=struct.pack('<I',count);at=data.find(token)
        while at>=0:
            if at+4+count*16<=len(data):
                rect=np.array([struct.unpack_from('<4f',data,at+4+j*16) for j in range(count)])
                if rect[0,1]>0 and rect[0,3]>0:
                    cols,rows=round(1/rect[0,1]),round(1/rect[0,3])
                    if cols>0 and rows>0 and cols*rows==count:
                        expected=np.array([[j%cols/cols,1/cols,j//cols/rows,1/rows] for j in range(count)])
                        if np.allclose(rect,expected,atol=1e-6):found.append((cols,rows,count))
            at=data.find(token,at+1)
    assert len(set(found))<=1,('存在歧义的源图集',found)
    return list(found[0]) if found else [1,1,1]

def export(a,path,start,phase_end=None,capacity_limit=256,sequence_name=None,legacy83=False,normalize=True):
    # 064仅显式调用的ALSshock启用LE83布局与mBegin，其他作者保持原默认路径和归一结果。
    # 同一爆炸的不同源层要在调用方统一缩放；normalize=False返回原游戏单位，不逐层放大。
    raw,strings=raw_blocks(path);doc=parse(path);blocks={b['index']:b for b in doc['parsed_blocks']};nodes={};systems={};emitters={};controllers={}
    for i,(kind,data) in raw.items():
        r=Reader(data)
        if kind in ('NiNode','BSFadeNode','NiBillboardNode','BSTriShape','NiParticleSystem','BSMasterParticleSystem'):
            name,ctl,m=av(r,strings);children=[r.read('i') for _ in range(r.read('I'))] if kind in ('NiNode','BSFadeNode','NiBillboardNode','BSMasterParticleSystem') else []
            nodes[i]={'name':name,'matrix':m,'children':children,'parent':-1}
            if kind=='NiParticleSystem':
                if legacy83:
                    # LE83的NiGeometry先带data/skin/材质列表，再到NiParticleSystem；绝不能套SSE100偏移。
                    data_id,skin,materials,active_material=r.read('4i');dirty=r.read('B');shader,alpha=r.read('2i')
                    assert materials==0 and active_material==0 and dirty==0
                    r.read('4H');world=r.read('B');mods=[r.read('i') for _ in range(r.read('I'))];r.done()
                else:
                    r.read('4f');skin,shader,alpha=r.read('3i');desc=r.read('Q');r.read('4H');data_id=r.read('i');world=r.read('B');mods=[r.read('i') for _ in range(r.read('I'))];r.done()
                assert skin==-1 and shader in blocks
                systems[i]={'name':name,'shader':shader,'alpha':alpha,'data':data_id,'mods':mods}
        elif kind in ('NiPSysCylinderEmitter','NiPSysSphereEmitter','NiPSysBoxEmitter'):
            name=r.read('I');order=r.read('I');target=r.read('i');active=r.read('B');v=r.read('6f');rgba=r.read('4f');radius,variation,life,lifevar=r.read('4f');obj=r.read('i')
            dims=r.read('2f' if kind.endswith('CylinderEmitter') else 'f' if kind.endswith('SphereEmitter') else '3f');r.done()
            emitters[i]={'kind':kind,'target':target,'speed':v[0],'variation':v[1],'declination':v[2],'declination_variation':v[3],'angle':v[4],'angle_variation':v[5],'radius':radius,'radius_variation':variation,'life':life,'life_variation':lifevar,'object':obj,'dimensions':dims}
        elif kind in ('NiPSysEmitterCtlr','BSPSysMultiTargetEmitterCtlr'):
            nxt=r.read('i');flags=r.read('H');freq,phase,begin,end=r.read('4f');target=r.read('i');ip=r.read('i');name=strings[r.read('I')];visibility=r.read('i')
            if kind=='BSPSysMultiTargetEmitterCtlr':
                # niftools定义为MaxEmitters ushort后接MasterParticleSystem指针；本源指向根块0。
                maximum=r.read('H');master=r.read('i');assert 0<maximum<=20 and master==0
            r.done()
            controllers[target]={'index':i,'ip':ip,'visibility':visibility,'stop':end,'name':name}
    for n in nodes.values():
        for child in n['children']:
            if child in nodes:nodes[child]['parent']=next(i for i,v in nodes.items() if v is n)
    def world(i):
        n=nodes[i];return n['matrix'] if n['parent']<0 else world(n['parent'])@n['matrix']
    for i,b in blocks.items():
        if b['type']=='NiPSysMeshEmitter':
            emitters[i]={'kind':b['type'],'target':b['target'],'speed':b['speed'],'variation':b['speed_variation'],'radius':b['initial_radius'],'radius_variation':b['radius_variation'],'life':b['life_span'],'life_variation':b['life_span_variation'],'meshes':b['emitter_meshes'],'object':b['emitter_meshes'][0]}
    # sequence直接持有真实BirthRate/EmitterActive插值器，不能取NiBlend占位常量。
    for b in blocks.values():
        if sequence_name is not None and b.get('name')!=sequence_name:continue
        for c in b.get('controlled_blocks',[]):
            for control in controllers.values():
                if c['controller']==control['index']:
                    control['visibility' if c['interpolator_id']=='EmitterActive' else 'ip']=c['interpolator']
                    control['stop']=b['stop']
    def interp(ip,t,boolean=False):
        if boolean:
            kind,data=raw[ip];r=Reader(data);constant=r.read('B');data_id=r.read('i');r.done();d=blocks.get(data_id,{})
            return next((k['value'] for k in reversed(d.get('keys',[])) if k['time']<=t),constant)
        d=blocks.get(ip,{});return float(sample(blocks.get(d.get('data'),{}),t,d.get('constant',0)))
    def emitter_mesh(index):
        kind,data=raw[index];assert kind=='BSTriShape';r=Reader(data);av(r,strings);r.read('4f');r.read('3i');desc=r.read('Q');nt,nv=r.read('2H');size=r.read('I');stride=(desc&15)*4;assert size==nv*stride+nt*6
        points=[]
        for _ in range(nv):
            offset=r.pos;points.append(r.read('3f'));r.pos=offset+stride
        tris=np.asarray(r.read(str(nt*3)+'H')).reshape(nt,3);p=np.asarray(points);W=world(index);p=p@W[:3,:3].T+W[:3,3]
        normals=np.cross(p[tris[:,1]]-p[tris[:,0]],p[tris[:,2]]-p[tris[:,0]]);area=np.linalg.norm(normals,axis=1);normals/=np.maximum(area[:,None],1e-9);cdf=np.cumsum(area);cdf/=cdf[-1]
        return p,tris,normals,cdf
    rng=np.random.default_rng(284037);layers=[];maxlife=0
    for i,e in emitters.items():
        system=systems[e['target']];sh=blocks[system['shader']];colour=next(blocks[m] for m in system['mods'] if m in blocks and blocks[m]['type']=='BSPSysSimpleColorModifier')
        # 049范围层源NiPSysData容量302，调用方显式允许512；其他爆炸仍保持原256/512边界。
        capacity=struct.unpack_from('<H',raw[system['data']][1],4)[0];assert 0<capacity<=(512 if raw[0][0]=='BSMasterParticleSystem' else capacity_limit)
        control=controllers[e['target']];stop=min(4 if raw[0][0]=='BSMasterParticleSystem' else 3,max(.001,control['stop']));ts=np.linspace(0,stop,3001)
        rate=np.array([max(0,interp(control['ip'],float(t)))*bool(interp(control['visibility'],float(t),True)) for t in ts])
        integral=np.r_[0,np.cumsum((rate[:-1]+rate[1:])*.5*np.diff(ts))]
        count=min(capacity,int(integral[-1]));assert count>0,(path,system['name'],'无源发射')
        births=np.interp(np.arange(count)+.5,integral,ts)
        # 原ALS持续喷发约一秒，参考终结要求蓝相先完全结束；仅压缩出生窗口，不丢源火花或改变其半径。
        if phase_end is not None:
            reserve=max(.01,e['life']+abs(e['life_variation']))+.005
            available=max(.001,phase_end-start-reserve)
            births*=min(1,available/max(.001,float(births.max())))
        grid=atlas_layout(raw[system['data']][1]);atlas=grid[0]
        scales=[]
        for mod in system['mods']:
            if raw[mod][0]=='BSPSysScaleModifier':
                q=Reader(raw[mod][1]);q.read('III');q.read('B');n=q.read('I');s=np.array(q.read(str(n)+'f'));q.done();scales.append(s)
        sizecurve=np.ones(5)
        for s in scales:sizecurve*=np.interp(np.linspace(0,1,5),np.linspace(0,1,len(s)),s)
        W=world(e['object']);mesh=emitter_mesh(e['object']) if 'meshes' in e else None
        # 位置已经乘发射节点世界矩阵；半径和速度也必须进入同一空间。
        # 旧作者把方向归一后丢了NiAVObject缩放，火焰三倍/烟团二倍/闪光2.25倍都被缩小。
        system_scale=float(np.linalg.norm(world(e['target'])[:3,0]))
        assert np.isfinite(system_scale) and 0<system_scale<100
        e['system_scale']=system_scale
        rotation=None
        if raw[0][0]=='BSMasterParticleSystem':
            # 原火焰是角度附近的小范围摆动，不能一概0..2PI随机转成四处横躺的火苗。
            for mod in system['mods']:
                if raw[mod][0]=='NiPSysRotationModifier':
                    r=Reader(raw[mod][1]);r.read('III');r.read('B');speed,variation,angle,anglevar=r.read('4f');random_sign,random_axis=r.read('2B');axis=r.read('3f');r.done()
                    rotation={'speed':speed,'variation':variation,'angle':angle,'angle_variation':anglevar,'random_sign':random_sign,'random_axis':random_axis,'axis':axis}
        particles=[]
        for birth in births:
            if mesh is not None:
                points,tris,normals,cdf=mesh;tri=min(len(tris)-1,int(np.searchsorted(cdf,rng.random())));u,v=rng.random(2)
                if u+v>1:u,v=1-u,1-v
                f=points[tris[tri]];p=f[0]+(f[1]-f[0])*u+(f[2]-f[0])*v;direction=normals[tri]
            else:
                d=e['dimensions'];d=[d] if np.isscalar(d) else d
                if e['kind'].endswith('CylinderEmitter'):
                    angle=rng.uniform(0,math.tau);radius=math.sqrt(rng.random())*d[0];local=np.array([math.cos(angle)*radius,math.sin(angle)*radius,rng.uniform(-.5,.5)*d[1]])
                elif e['kind'].endswith('SphereEmitter'):
                    local=rng.normal(size=3);local/=np.linalg.norm(local);local*=d[0]*rng.random()**(1/3)
                else:local=(rng.random(3)-.5)*np.asarray(d)
                p=W[:3,:3]@local+W[:3,3]
                decl=e['declination']+rng.uniform(-e['declination_variation'],e['declination_variation']);angle=e['angle']+rng.uniform(-e['angle_variation'],e['angle_variation'])
                direction=W[:3,:3]@np.array([math.sin(decl)*math.cos(angle),math.sin(decl)*math.sin(angle),math.cos(decl)]);direction/=max(1e-9,np.linalg.norm(direction))
            velocity=direction*max(0,e['speed']+rng.uniform(-e['variation'],e['variation']))*system_scale
            life=max(.01,e['life']+rng.uniform(-e['life_variation'],e['life_variation']))
            birth=float(birth)+start
            if phase_end is not None:life=min(life,max(.01,phase_end-birth))
            radius=max(.01,e['radius']+rng.uniform(-e['radius_variation'],e['radius_variation']))
            p=a.a.C@p*a.a.SCALE;velocity=a.a.C@velocity*a.a.SCALE;radius*=a.a.SCALE*system_scale
            particles.append([*p.tolist(),*velocity.tolist(),birth,life,radius,float(rotation['angle']+rng.uniform(-rotation['angle_variation'],rotation['angle_variation']) if rotation else rng.uniform(0,math.tau))])
            maxlife=max(maxlife,birth+life)
        acceleration=np.zeros(3);forces=[]
        # 040仅对这两个实际MPS读取明确的匀强重力。零衰减/零扰动/未被开关控制的方向力可精确积分。
        # 其余空间拖曳、湍流及受控力只登记未移植，不能凭主观加一股“升腾”风冒充源文件。
        if raw[0][0]=='BSMasterParticleSystem':
            controlled=set()
            for kind,data in raw.values():
                if kind=='NiPSysModifierActiveCtlr':
                    c=Reader(data);c.read('iH4f');target=c.read('i');c.read('i');controlled.add((target,strings[c.read('I')]))
            for index in system['mods']:
                kind,data=raw[index]
                if kind!='NiPSysGravityModifier':continue
                r=Reader(data);name=strings[r.read('I')];r.read('I');target=r.read('i');active=r.read('B');obj=r.read('i');axis=np.asarray(r.read('3f'));decay,strength=r.read('2f');form=r.read('I');turbulence,turbscale=r.read('2f');aligned=r.read('B');r.done()
                supported=bool(active and form==0 and decay==0 and turbulence==0 and (target,name) not in controlled)
                forces.append({'name':name,'axis':axis.tolist(),'strength':strength,'decay':decay,'type':form,'turbulence':turbulence,'world_aligned':bool(aligned),'constant_applied':supported})
                if supported:
                    direction=axis if aligned else world(obj)[:3,:3]@axis
                    direction/=max(1e-9,np.linalg.norm(direction));acceleration+=a.a.C@direction*strength*a.a.SCALE
        # 颜色/梯度/图集来自独立原始发射器；不是把地震平面改色后当爆炸。
        blend='src_alpha one'
        if system['alpha']>=0:
            r=Reader(raw[system['alpha']][1]);r.read('I');[r.read('i') for _ in range(r.read('I'))];r.read('i');flags=r.read('H')
            blend='src_alpha one_minus_src_alpha' if ((flags>>5)&15)==7 else 'src_alpha one'
        spec={'opaque':False,'particle':True,'burst_particle':True,'texture':a.texture(sh['source_texture']),'palette':a.texture(sh['palette_texture']),'has_palette':bool(sh['palette_texture']),'shader_flags':sh['shader_flags'],'atlas':atlas,'atlas_grid':grid,'ion_blue':phase_end is not None,'base_color':sh['base_color'],'grey_color':bool(sh['palette_texture'] and sh['shader_flags'][0]&16),'grey_alpha':bool(sh['palette_texture'] and sh['shader_flags'][0]&32),'gain':sh['base_color_scale'],'uv':sh['uv_offset']+sh['uv_scale'],'colors':colour['colors'],'intervals':colour['color_intervals'],'fade_in':colour['fade_in_percent'],'fade_out':colour['fade_out_percent'],'size_curve':sizecurve.tolist(),'blend':blend}
        name='IrisArsenal/DrillBurst/'+path.stem+'/'+str(i);a.MATS[name]=spec
        layers.append({'name':system['name'],'material':name,'particles':particles,'source_capacity':capacity,'size_curve':sizecurve.tolist(),'source_emitter':i,'source_parameters':e,'source_forces':forces,'source_rotation':rotation,'acceleration':acceleration.tolist(),'atlas':atlas,'atlas_grid':grid})
    bounds=[]
    for layer in layers:
        for p in layer['particles']:
            center=np.array(p[:3]);velocity=np.array(p[3:6]);extent=p[8]*max(layer['size_curve'])*math.sqrt(2)
            # 混合正负坐标时，只有两条对角端点会低估包围球；覆盖全部八角，防止相机边缘被错误裁掉。
            for point in (center,center+velocity*p[7]):
                bounds.extend([point+np.asarray(sign)*extent for sign in itertools.product((-1,1),repeat=3)])
    q=np.array(bounds);source_peak=float(np.linalg.norm(q,axis=1).max());assert source_peak>0 and maxlife<8
    peak=source_peak if normalize else 1.
    # 同一组在3D中统一归一，不压扁Y轴；相机朝向仅用于每一张源粒子卡片。
    for layer in layers:
        for p in layer['particles']:
            for k in range(6):p[k]/=peak
            p[8]/=peak
        layer['acceleration']=(np.asarray(layer['acceleration'])/peak).tolist()
        a.MATS[layer['material']]['acceleration']=layer['acceleration']
    return layers,{'source':str(path),'sha256':a.a.sha(path),'start':start,'phase_end':phase_end,'life':maxlife,'source_peak':peak,'unnormalized_peak':source_peak,'sequence':sequence_name,'legacy83':legacy83,'bounds':(q/peak).tolist(),'layers':layers,'adaptation':'有界源容量/发射率积分/发射体/原图集/原渐变/五点尺寸曲线；固定随机种子、匀速展开；未完整模拟源拖曳/重力/风场'}

def submesh(a,layer):
    if 'size_curve17' in layer:
        import muzzle_detail
        return muzzle_detail.submesh(a,layer)
    verts=[];indices=[]
    for p in layer['particles']:
        base=len(verts);verts.extend([(*p[:6],*p[6:],u,v) for u,v in ((0,0),(1,0),(1,1),(0,1))]);indices.extend([base,base+1,base+2,base,base+2,base+3])
    decl=a.a.chunk(0x5100,b''.join(a.a.chunk(0x5110,struct.pack('<5H',0,t,s,o,0)) for t,s,o in ((2,1,0),(2,4,12),(3,5,24),(1,7,40))))
    vb=b''.join(struct.pack('<12f',*p) for p in verts)
    geom=a.a.chunk(0x5000,struct.pack('<I',len(verts))+decl+a.a.chunk(0x5200,struct.pack('<HH',0,48)+a.a.chunk(0x5210,vb)))
    raw=a.a.chunk(0x4000,layer['material'].encode()+b'\n'+struct.pack('<?I?',False,len(indices),False)+struct.pack('<%dH'%len(indices),*indices)+geom)
    return raw,np.asarray([p[:3] for p in verts])

SHADER=r"""
// 有限源爆炸粒子：位置/速度、生存期/半径/转角均来自离线作者；独立游戏秒，不访问角色/物理场景。
VOut iris_burst_vp(VIn i,uniform float4x4 wvp,uniform float4x4 inverseWorldView,uniform float4 clock,uniform float4 atlas,uniform float4 frameInset,uniform float4 sizeCurve,uniform float4 sizeEnd,uniform float4 color0,uniform float4 color1,uniform float4 color2,uniform float4 intervals,uniform float4 fades,uniform float4 uvBase,uniform float3 sourceAcceleration){
 VOut o;float elapsed=clock.x-i.c.x,life=max(.001,i.c.y),t=saturate(elapsed/life);float active=step(0,elapsed)*(1-step(life,elapsed));
 float x=t*4;float size=x<1?lerp(sizeCurve.x,sizeCurve.y,x):x<2?lerp(sizeCurve.y,sizeCurve.z,x-1):x<3?lerp(sizeCurve.z,sizeCurve.w,x-2):lerp(sizeCurve.w,sizeEnd.x,x-3);
 float4 color=t<intervals.y?lerp(color0,color1,saturate((t-intervals.x)/max(.001,intervals.y-intervals.x))):t<intervals.z?color1:lerp(color1,color2,saturate((t-intervals.z)/max(.001,intervals.w-intervals.z)));
 // 源Color区间只决定RGB；透明度走独立fade百分比，不能再随RGB区间提前归零并乘第二次淡出。
 float alphaIn=lerp(color0.a,color1.a,saturate(t/max(.001,fades.x)));
 float alphaOut=lerp(color1.a,color2.a,saturate((t-(1-fades.y))/max(.001,fades.y)));
 color.a=(t<fades.x?alphaIn:t>1-fades.y?alphaOut:color1.a)*active*clock.y;
 // 与引擎其他实体统一走worldviewproj；在物体空间构建朝向相机的卡片，避免另拼世界/投影矩阵。
 // 源匀强方向重力按游戏年龄积分；默认0保持旧ALS/覆盖层，无墙钟噪声或自拟运动。
 float et=max(0,elapsed);float3 center=i.p.xyz+i.n*et+.5*sourceAcceleration*et*et;float2 corner=(i.uv*2-1)*i.c.z*size;
 float cs=cos(i.c.w),sn=sin(i.c.w);corner=float2(cs*corner.x-sn*corner.y,sn*corner.x+cs*corner.y);
 float3 right=normalize(float3(inverseWorldView[0][0],inverseWorldView[1][0],inverseWorldView[2][0])),up=normalize(float3(inverseWorldView[0][1],inverseWorldView[1][1],inverseWorldView[2][1]));
 o.p=mul(wvp,float4(center+right*corner.x+up*corner.y,1));o.c=color;
 // 矩形图集逐帧插值；半纹素内缩防止线性过滤混入相邻格，绝不把整张接触表铺在巨型面上。
 float frame=t*max(0,atlas.z-1),f0=floor(frame),f1=min(atlas.z-1,f0+1);float2 grid=max(float2(1,1),atlas.xy);
 float2 local=clamp(i.uv/grid,frameInset.xy,1/grid-frameInset.xy);
 float2 uv0=local+float2(fmod(f0,grid.x),floor(f0/grid.x))/grid,uv1=local+float2(fmod(f1,grid.x),floor(f1/grid.x))/grid;
 o.uv=uv0*uvBase.zw+uvBase.xy;o.n=float3(uv1*uvBase.zw+uvBase.xy,frac(frame));o.view=0;return o;
}
// 源NiBillboardNode的两层薄闪光：先应用本层动画，再绕其中心朝向相机；不转角色或相机。
VOut iris_burst_card_vp(VIn i,uniform float4x4 wvp,uniform float4x4 worldMatrix,uniform float4x4 inverseWorldView,uniform float3 cameraPosition,uniform float4 clock,uniform float4 delta0,uniform float4 delta1,uniform float4 delta2,uniform float3 cardCenter){
 VOut o;float3 p=i.p.xyz,center=cardCenter;
 if(clock.z>.5){p=float3(dot(delta0,i.p),dot(delta1,i.p),dot(delta2,i.p));float4 c=float4(center,1);center=float3(dot(delta0,c),dot(delta1,c),dot(delta2,c));}
 float3 right=normalize(float3(inverseWorldView[0][0],inverseWorldView[1][0],inverseWorldView[2][0])),up=normalize(float3(inverseWorldView[0][1],inverseWorldView[1][1],inverseWorldView[2][1]));
 float3 q=center+right*(p.x-center.x)+up*(p.z-center.z);
 o.p=mul(wvp,float4(q,1));o.c=i.c;o.uv=i.uv;o.view=cameraPosition-mul(worldMatrix,float4(q,1)).xyz;o.n=o.view;return o;
}
float4 iris_burst_fp(VOut i,uniform float4 burstFlags,uniform float4 burstTint,uniform float4 burstProfile):SV_Target {
 // palette存在与源Greyscale开关分开；继承源基色/alpha，LUT边界由clamp采样防止y=1绕回黑行。
 // 无论LUT在alpha=0行存什么，未出生/已死亡的粒子必须严格不可见。
 clip(i.c.a-.00001);float4 texel=lerp(t0.Sample(s0,i.uv),t0.Sample(s0,i.n.xy),i.n.z);float3 rgb=burstFlags.x>.5?t1.Sample(s1,saturate(float2(texel.g,i.c.g*burstTint.r))).rgb:texel.rgb*i.c.rgb*burstTint.rgb;
 float alpha=texel.a*i.c.a*burstTint.a;if(burstFlags.y>.5)alpha=t1.Sample(s1,saturate(float2(texel.a,i.c.a*burstTint.a))).a*i.c.a*burstTint.a;
 // 原版档案的这张LUT偏暖；按用户原录像对电离层做蓝色显示适配，源纹理细节/alpha保持。
 if(burstFlags.w>.5)rgb=dot(rgb,float3(.2126,.7152,.0722))*float3(.24,.60,1.6);
 // 覆盖层提起原贴图的弱边缘，保持中心细节；原七发射器默认gamma=1/mult=1，不改变其层次。
 alpha=saturate(pow(saturate(alpha),max(.1,burstProfile.x))*burstProfile.y);
 clip(alpha-.002);return float4(rgb*burstFlags.z,alpha);
}
"""

def material(name,d,textures):
    # 使用真实贴图尺寸，不放大/插值伪造清晰度；矩形帧的像素与原档案完全一致。
    from PIL import Image
    from io import BytesIO
    pixels=textures[d['texture']];width,height=Image.open(BytesIO(pixels)).size
    grid=d.get('atlas_grid',[d['atlas'],d['atlas'],d['atlas']**2])
    v=lambda x:' '.join('%.9f'%n for n in x)
    acceleration=d.get('acceleration',[0,0,0])
    # 两纹理显式绑定，阴影/深度写关闭；透明混合仍遵守该源粒子层原设置。
    text='material '+name+'\n{\n technique { pass {\n lighting off\n depth_check on\n depth_write off\n cull_hardware none\n scene_blend '+d['blend']+'\n vertex_program_ref IrisBurstVP {\n param_named sourceAcceleration float3 '+v(acceleration)+'\n param_named atlas float4 '+v(grid+[0])+'\n param_named frameInset float4 '+v([.5/width,.5/height,0,0])+'\n param_named sizeCurve float4 '+v(d['size_curve'][:4])+'\n param_named sizeEnd float4 '+str(d['size_curve'][4])+' 0 0 0\n'+''.join(' param_named color%d float4 %s\n'%(i,v(c)) for i,c in enumerate(d['colors']))+' param_named intervals float4 '+v(d['intervals'])+'\n param_named fades float4 '+v([d['fade_in'],d['fade_out'],0,0])+'\n param_named uvBase float4 '+v(d['uv'])+'\n }\n fragment_program_ref IrisBurstFP { param_named burstFlags float4 '+v([int(d['grey_color']),int(d['grey_alpha']),d['gain'],int(d.get('ion_blue',False))])+'\n param_named burstTint float4 '+v(d['base_color'])+'\n param_named burstProfile float4 '+v(d.get('profile',[1,1,0,0]))+' }\n texture_unit { texture '+d['texture']+' }\n texture_unit { texture '+d['palette']+'\n tex_address_mode clamp\n }\n } }\n}\n'

    if d.get('muzzle_detail'):
        import muzzle_detail
        return muzzle_detail.material(text,d)
    return text

PROGRAM="""
vertex_program IrisBurstVP hlsl
{
 source iris_eight.hlsl
 entry_point iris_burst_vp
 target vs_4_0
 default_params {
 param_named_auto wvp worldviewproj_matrix
 param_named_auto inverseWorldView inverse_worldview_matrix
 param_named_auto clock custom 1
 }
}
vertex_program IrisBurstCardVP hlsl
{
 source iris_eight.hlsl
 entry_point iris_burst_card_vp
 target vs_4_0
 default_params {
 param_named_auto wvp worldviewproj_matrix
 param_named_auto worldMatrix world_matrix
 param_named_auto inverseWorldView inverse_worldview_matrix
 param_named_auto cameraPosition camera_position
 param_named_auto clock custom 1
 param_named_auto delta0 custom 5
 param_named_auto delta1 custom 6
 param_named_auto delta2 custom 7
 }
}
fragment_program IrisBurstFP hlsl
{
 source iris_eight.hlsl
 entry_point iris_burst_fp
 target ps_4_0
}
"""
