
# 070：移除已由AST与跨模块引用核实的未使用导入；原资源生产算法保持。
"""十招源网格/贴图/控制器准备；不能直接执行Skyrim粒子或屏幕折射，限制逐层登记。"""
from pathlib import Path
from io import BytesIO
import copy,hashlib,json,struct,re,sys
import numpy as np
from PIL import Image
import author_prototype as a
import nif_reader as nr
from safeio import ROOT,put
from read_bsa import archive_file
from read_legacy_nif import read_legacy
from fx_timeline import timeline
import author_reticle
import fx_optics
import drill_finisher
import fire_optics
import iris_wings
import drill_particles
import muzzle_detail
import electro_area
A=a.ASSET;S=a.SOURCE;BASE=Path('E:/skyrimspecialedition/SkyrimSE/Data')
ELDEN=Path('E:/skyrimspecialedition/mods/0-Elden Rim-Base 3.5.9')
TEXTURES={};MATS={};PROVENANCE=[]
def texture(ref):
    if not ref:return 'iris_white.dds'
    raw=ref.replace('\\','/');match=re.search('(?i)(?:^|/)textures/',raw);assert match,ref
    tail=raw[match.start():].lstrip('/');p=S/tail;data=p.read_bytes() if p.is_file() else None;source=str(p)
    if data is None and (ELDEN/tail).is_file():
        p=ELDEN/tail;data=p.read_bytes();source=str(p)
    if data is None:
        for bsa in sorted(BASE.glob('Skyrim - Textures*.bsa')):
            data=archive_file(bsa,tail)
            if data is not None:source=str(bsa)+'::'+tail;break
    assert data is not None,('源贴图未找到',ref)
    digest=hashlib.sha256(data).hexdigest();name='iris_fx_'+digest[:16]+'.png'
    # 普通武器/钻头已经使用同字节RGBA转换；GPU按资源文件名缓存，另起名字会再驻留约21.3MiB。
    # 只对已验证的源摘要共享命名，保持2048原像素、RGBA和材质参数，不换回不兼容的BC7 DDS。
    if digest.startswith('179f128b96e16ff2'):name='iris_anim_rgba_'+digest[:16]+'.png'

    im=Image.open(BytesIO(data)).convert('RGBA');out=BytesIO();im.save(out,format='PNG')
    assert np.array_equal(np.asarray(im),np.asarray(Image.open(BytesIO(out.getvalue())).convert('RGBA')))
    TEXTURES[name]=out.getvalue();PROVENANCE.append({'reference':ref,'source':source,'sha256':digest,'output':name,'same_pixels':True})
    return name

def sample_curve(blocks,controller,t,default):
    c=blocks.get(controller,{});ip=blocks.get(c.get('interpolator'),{});data=blocks.get(ip.get('data'),{});ks=data.get('keys',[])
    if not ks:return ip.get('constant',default)
    # NiFloatData二次插值保留源前后切线；端点钳位，不把源constant哨兵当实际数值。
    time=t*c.get('frequency',1)+c.get('phase',0)
    if time<=ks[0]['time']:return ks[0]['value']
    if time>=ks[-1]['time']:return ks[-1]['value']
    j=next(i for i in range(len(ks)-1) if ks[i]['time']<=time<ks[i+1]['time']);x,y=ks[j:j+2];u=(time-x['time'])/(y['time']-x['time'])
    v=np.asarray(x['value']);w=np.asarray(y['value'])
    if data.get('interpolation')==2:
        v=(2*u**3-3*u*u+1)*v+(u**3-2*u*u+u)*np.asarray(x['forward'])+(-2*u**3+3*u*u)*w+(u**3-u*u)*np.asarray(y['backward'])
    else:v=v*(1-u)+w*u
    return v.tolist() if v.ndim else float(v)

def controller_constants(shader,blocks):
    effect=shader.get('effect');alpha=shader.get('alpha',1);uv=shader['uv_offset']+shader['uv_scale'];colour=[1,1,1];scroll=[0,0]
    if not effect:return alpha,uv,colour,scroll
    colour=effect['base_color'][:3];i=effect['controller'];seen=set()
    # 源多层出生alpha=0，由控制器点亮。读取曲线的峰值作为有界包络上限，运行时age负责出生/消退。
    while i>=0:
        assert i not in seen;seen.add(i);c=blocks.get(i,{});variable=c.get('variable');data=blocks.get(blocks.get(c.get('interpolator'),{}).get('data'),{});keys=data.get('keys',[])
        if 'FloatController' in c.get('type',''):
            if variable==5 and keys:alpha=max(float(k['value']) for k in keys)
            if variable in (6,8) and len(keys)>1:
                span=keys[-1]['time']-keys[0]['time'];scroll[0 if variable==6 else 1]=(keys[-1]['value']-keys[0]['value'])/max(span,1e-6)*c.get('frequency',1)
        if 'ColorController' in c.get('type','') and keys:
            colour=max((k['value'] for k in keys),key=lambda v:sum(v))
        i=c.get('next',-1)
    return max(0,min(1,alpha)),uv,colour,scroll

def material(mesh,blocks,presentation=(1,1)):
    sh=mesh['shader_data'];effect=sh.get('effect');opaque=not effect and mesh['alpha_data'] is None
    alpha,uv,colour,scroll=controller_constants(sh,blocks)
    # 源Greyscale-to-Palette的BaseColor.r是查表纵坐标，不能把整张调色图乘红色或固定取y=0.5。
    # source没有调色图/贴图时分别走源基色/白采样；保留顶点RGB和alpha各自的开关。
    flags=effect['shader_flags'] if effect else sh.get('flags',[0,0])
    if effect:
        emission=list(colour);gain=effect['base_color_scale'];palette=texture(effect['palette_texture']);diffuse=texture(effect['source_texture'])
    else:
        emission=[v*sh['emissive_mult'] for v in sh['emissive']];gain=1;palette='iris_white.dds';diffuse=texture(mesh['textures'][0])
    ap=mesh['alpha_data'];bits=ap['flags'] if ap else 0
    blend_names={0:'one',1:'zero',2:'src_colour',3:'one_minus_src_colour',4:'dest_colour',5:'one_minus_dest_colour',6:'src_alpha',7:'one_minus_src_alpha',8:'dest_alpha',9:'one_minus_dest_alpha'}
    blend='one zero'
    if bits&1:
        src=(bits>>1)&15;dst=(bits>>5)&15
        assert src in blend_names and dst in blend_names,('不支持的源混合模式',bits)
        blend=blend_names[src]+' '+blend_names[dst]
    # 脉冲命中特效独立的显示增益，不改源控制曲线或其他技能共享材质；倍率与碰撞不受影响。
    spec={'opaque':opaque,'emission':emission,'alpha':alpha,'uv':uv,'scroll':scroll,'diffuse':diffuse,'palette':palette,'effect':bool(effect),'source_alpha':ap,
          'blend':blend,'source_shader_flags':list(flags),'grey_color':bool(effect and effect['palette_texture'] and flags[0]&16),
          'grey_alpha':bool(effect and effect['palette_texture'] and flags[0]&32),'vertex_color':bool(flags[1]&32),'vertex_alpha':bool(flags[0]&8),
          'falloff':list(effect['falloff']) if effect else [1,0,1,1],'use_falloff':bool(effect and flags[0]&64),'gain':gain,
          'has_source':bool(effect['source_texture']) if effect else True,'has_palette':bool(effect and effect['palette_texture']),
          'alpha_cutoff':ap['threshold']/255 if ap and bits&512 else .002}
    # 源翼片单独纳入材质哈希，避免升级其镜面时改变其他招式复用的材质。
    if mesh.get('wing_source_metal'):spec['wing_metal']=mesh['wing_source_metal']
    if presentation!=(1,1):spec['presentation']=list(presentation)
    name='IrisArsenal/Eight/'+hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest()[:14];MATS[name]=spec;return name

def mesh_bytes(meshes,blocks,presentation=(1,1)):
    subs=[];bounds=[];mats=[]
    for x in meshes:
        p=(np.array(x['vertices'])@x['matrix'][:3,:3].T+x['matrix'][:3,3])@a.C.T*a.SCALE
        n=np.array(x['normals'])@np.linalg.inv(x['matrix'][:3,:3])@a.C.T;n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-10)
        colours=x['colours'] or [(1,1,1,1)]*len(p);bounds.extend(p);name=material(x,blocks,presentation);mats.append(name)
        # 明确保留源顶点RGBA；32字节旧路径会丢边缘alpha。新声明为48字节FLOAT4颜色，消费端专用VP。
        decl=a.chunk(0x5100,b''.join(a.chunk(0x5110,struct.pack('<5H',0,t,s,o,0)) for t,s,o in [(2,1,0),(2,4,12),(3,5,24),(1,7,40)]))
        vb=b''.join(struct.pack('<12f',*pos,*norm,*c,*uv) for pos,norm,c,uv in zip(p,n,colours,x['uv']))
        geom=a.chunk(0x5000,struct.pack('<I',len(p))+decl+a.chunk(0x5200,struct.pack('<HH',0,48)+a.chunk(0x5210,vb)))
        idx=[i for tri in x['triangles'] for i in tri];assert len(p)<65536
        subs.append(a.chunk(0x4000,name.encode()+b'\n'+struct.pack('<?I?',False,len(idx),False)+struct.pack('<%dH'%len(idx),*idx)+geom))
    p=np.array(bounds);assert len(p)
    return b'\x00\x10[MeshSerializer_v1.41]\n'+a.chunk(0x3000,b'\0'+b''.join(subs)+a.chunk(0x9000,struct.pack('<7f',*p.min(0),*p.max(0),np.linalg.norm(p,axis=1).max()))),mats,p

SHADER=r"""// Iris源光学适配：分别保留调色图、源混合、顶点RGB/alpha、视角衰减；时钟来自游戏秒。
struct VIn {float4 p:POSITION;float3 n:NORMAL;float4 c:COLOR;float2 uv:TEXCOORD0;};
struct VOut {float4 p:SV_Position;float4 c:COLOR;float2 uv:TEXCOORD0;float3 n:TEXCOORD1;float3 view:TEXCOORD2;};
VOut iris_eight_vp(VIn i,uniform float4x4 wvp,uniform float4x4 normalMatrix,uniform float4x4 worldMatrix,uniform float3 cameraPosition,uniform float4 clock,uniform float4 delta0,uniform float4 delta1,uniform float4 delta2){
 // 每层只变换插件自己导出的几何；角色、TagPoint和物理场景坐标不被写入。
 if(clock.z>.5){i.p=float4(dot(delta0,i.p),dot(delta1,i.p),dot(delta2,i.p),1);float3 c0=cross(delta1.xyz,delta2.xyz),c1=cross(delta2.xyz,delta0.xyz),c2=cross(delta0.xyz,delta1.xyz);float det=dot(delta0.xyz,c0);if(abs(det)>.0000001)i.n=float3(dot(c0,i.n),dot(c1,i.n),dot(c2,i.n))/det;}
 VOut o;o.p=mul(wvp,i.p);o.c=i.c;o.uv=i.uv;o.n=mul((float3x3)normalMatrix,i.n);o.view=cameraPosition-mul(worldMatrix,i.p).xyz;return o;
}
Texture2D t0:register(t0);Texture2D t1:register(t1);SamplerState s0:register(s0);SamplerState s1:register(s1);
float4 iris_eight_fp(VOut i,uniform float4 clock,uniform float4 uvBase,uniform float4 uvFlow,uniform float4 tint,uniform float4 flags,uniform float4 vertexFlags,uniform float4 effectParams,uniform float4 falloff,uniform float4 sourceTint,uniform float4 sourceUV,uniform float4 sourceMisc,uniform float4 sourceFalloff,uniform float4 presentation):SV_Target {
 if(clock.z>.5){tint=sourceTint;uvBase=sourceUV;uvFlow=0;effectParams.x=sourceMisc.x;falloff=sourceFalloff;}
 float2 uv=i.uv*uvBase.zw+uvBase.xy+uvFlow.xy*clock.x;
 float4 texel=effectParams.y>.5?t0.Sample(s0,uv):float4(1,1,1,1);
 float4 vertex=float4(vertexFlags.x>.5?i.c.rgb:float3(1,1,1),vertexFlags.y>.5?i.c.a:1);
 float fade=1;
 if(vertexFlags.z>.5){float width=falloff.x-falloff.y;float u=abs(width)>.00001?saturate((abs(dot(normalize(i.n+0.00001),normalize(i.view+0.00001)))-falloff.y)/width):1;u=u*u*(3-2*u);fade=lerp(max(0,falloff.w),min(1,falloff.z),u);}
 float3 rgb;float alpha;
 if(flags.x>.5){
  // 颜色与alpha分别查表：绿通道驱动颜色索引，BaseColor.r/顶点绿驱动纵坐标；无palette绝不取黑回退图。
  rgb=flags.z>.5?t1.Sample(s1,saturate(float2(texel.g,vertex.g*fade*tint.r))).rgb:texel.rgb*vertex.rgb*tint.rgb;
  alpha=texel.a*vertex.a*fade*tint.a*tint.a;
  if(flags.w>.5)alpha=t1.Sample(s1,saturate(float2(texel.a,vertex.a*fade*tint.a*tint.a))).a;
  rgb*=effectParams.x;
 }else{
  rgb=texel.rgb*(1+tint.rgb)*vertex.rgb;alpha=flags.y>.5?1:texel.a*tint.a*vertex.a;
  if(flags.y>.5)rgb*=.35+.65*abs(dot(normalize(i.n+0.00001),normalize(float3(.3,.8,.5))));
 }
 // 显示增益最后施加：源UV/调色/层次照常，避免把整套脉冲烘成统一颜色。
 // 用户新参考要求白紫束芯；仅光炮专用材质转换源能量亮度，其他火焰/脉冲调色不受影响。
 if(presentation.z>.5){float lum=dot(rgb,float3(.2126,.7152,.0722));float hot=saturate(lum*.45);rgb=lerp(float3(.12,.22,.8),float3(.9,.85,1.12),hot)*max(.7,lum);}
 // 仅ALS电离层按原录像冷蓝显示；其他技能与火焰材质不参与此适配。
 if(presentation.w>.5)rgb=dot(rgb,float3(.2126,.7152,.0722))*float3(.24,.60,1.6);
 alpha=saturate(alpha*presentation.x)*clock.y;rgb*=presentation.y;clip(alpha-max(.002,vertexFlags.w));return float4(rgb,alpha);
}
"""

TRAIL_FP=r"""// ManualObject的轨迹使用独立静态VP，不声明不存在的Entity custom参数。
VOut iris_trail_vp(VIn i,uniform float4x4 wvp,uniform float4x4 normalMatrix,uniform float4x4 worldMatrix,uniform float3 cameraPosition){
 VOut o;o.p=mul(wvp,i.p);o.c=i.c;o.uv=i.uv;o.n=mul((float3x3)normalMatrix,i.n);o.view=cameraPosition-mul(worldMatrix,i.p).xyz;return o;
}
// 实际武器历史几何；源尾焰纹理/梯度，透明度由历史年龄给出，不走GPU墙钟。
float4 iris_trail_fp(VOut i):SV_Target {
 float4 mask=t0.Sample(s0,i.uv);float4 grad=t1.Sample(s1,float2(saturate(mask.r),.5));
 float alpha=mask.a*i.c.a;clip(alpha-.002);return float4(grad.rgb*2,alpha);
}
"""

def weapon_proxy():
    # 实体正常网格8截面，和运行时/离线覆盖共用，不用length或枪口外延猜测。
    meshes,_=a.read_nif(S/'Meshes/SW/Iris/2.nif')
    points=np.concatenate([(np.asarray(x['vertices'])@x['matrix'][:3,:3].T+x['matrix'][:3,3])@a.C.T*a.SCALE for x in meshes]);sections=[]
    for lo,hi in zip(np.linspace(points[:,2].min(),points[:,2].max(),9)[:-1],np.linspace(points[:,2].min(),points[:,2].max(),9)[1:]):
        p=points[(points[:,2]>=lo-1e-5)&(points[:,2]<=hi+1e-5)];assert len(p);center=(p[:,:2].min(0)+p[:,:2].max(0))*.5;radius=float(np.linalg.norm(p[:,:2]-center,axis=1).max());sections.append([*center,float(lo),float(hi),radius])
    put(A/'weapon_collision.csv','IRIS_WEAPON_CAPSULES 1 8\n'+'\n'.join(' '.join('%.9f'%v for v in x) for x in sections)+'\n','正常武器碰撞作者','8个真实源截面，完整producer/consumer配套')

def normalize_beam(meshes,d,longitudinal_only=False):
    # 五层源管统一到r<=1、z=0..1，消费者直接用R9/有效长度缩放；所有源层仍保留UV和相对结构。
    points=[];H=np.eye(4);H[:3,:3]=a.C*a.SCALE
    for mesh,tr in zip(meshes,d['tracks']):
        p=(np.asarray(mesh['vertices'])@mesh['matrix'][:3,:3].T+mesh['matrix'][:3,3])@a.C.T*a.SCALE
        points.append(p)
        for state in tr['frames']:
            m=np.array(state[13:]).reshape(3,4);points.append(p@m[:,:3].T+m[:,3])
    q=np.concatenate(points);radius=float(np.linalg.norm(q[:,:2],axis=1).max());lo=float(q[:,2].min());length=float(np.ptp(q[:,2]));assert radius>0 and length>0
    # 电脉保留原横截面，只把长度归一供用户前20/R25的近战终点消费；远程仍用原路径。
    if longitudinal_only:radius=1.
    N=np.diag([1/radius,1/radius,1/length,1.]);N[2,3]=-lo/length;Ni=np.linalg.inv(N);normalized=copy.deepcopy(meshes);points=[]
    for mesh,tr in zip(normalized,d['tracks']):
        mesh['matrix']=np.linalg.inv(H)@N@H@mesh['matrix']
        p=(np.asarray(mesh['vertices'])@mesh['matrix'][:3,:3].T+mesh['matrix'][:3,3])@a.C.T*a.SCALE
        for state in tr['frames']:
            m=np.eye(4);m[:3]=np.array(state[13:]).reshape(3,4);m=N@m@Ni;state[13:]=m[:3].reshape(-1).tolist();points.append(p@m[:3,:3].T+m[:3,3])
    q=np.concatenate(points);d['bounds']=[q.min(0).tolist(),q.max(0).tolist()];d['peak_radius']=float(np.linalg.norm(q,axis=1).max());d['cylinder_normalization']={'source_radius':radius,'source_z_min':lo,'source_length':length,'target_radius':1,'target_z':[0,1]}
    return normalized

import fire_burst

def canonical_provenance(rows,materials):
    # 052去掉无效heavy后，仅保留实际材质引用的来源并精确去重，排序固定；不改任何纹理像素或材质参数。
    active={d.get(key) for d in materials.values() for key in ('diffuse','palette','texture') if d.get(key)}
    return [json.loads(value) for value in sorted({json.dumps(row,sort_keys=True,ensure_ascii=False) for row in rows if row['output'] in active})]

def main():
    weapon_proxy();assets=[];curves={}
    for key,file in [('gun','anim.nif'),('blade','charge2.nif'),('shell','PlasmaBall.nif'),('blast','explosionwarm0.nif'),('shock','explosionwarm0.nif'),('exhaust','backfire.nif'),('beam','beam.nif'),('bullet','FireballProjectile01.nif'),('pulse_blast','RimMagicdlc1aurielsskyboltexplosion01.nif'),('muzzle','shoutareaexplosionwarm0.nif'),('fire_blast','explosionwarm0.nif'),('roll_blast','VoiceFlameWaveProject03.nif'),('full_blast','VoiceFlameWaveProject03.nif'),('electro_burst','beam.nif'),('muzzle_fire','SW_MagMuzzle.nif'),('charge_halo','charge3.nif')]:
        # 040严格复用FullBust_End真实火浪与其ADDN64对象；枪口单独沿NAM1/ADDN09。
        if key=='muzzle_fire':
            asset,curves[key]=fire_burst.muzzle(sys.modules[__name__]);assets.append(asset);continue
        if key in ('fire_blast','roll_blast','full_blast'):
            asset,curves[key]=fire_burst.standalone(sys.modules[__name__],key);assets.append(asset);continue
        # source-cache是从本机原版BSA只读抽取的同字节火球；非滚5源文件改写。
        path=ROOT/'tools/source-cache'/file if key=='bullet' else ELDEN/('meshes/RimMagic/'+file) if key=='pulse_blast' else S/('Meshes/SW/Iris/'+file)
        if key=='muzzle':
            # 旧四层ShoutArea球体不是录像准星；改用参考帧约束的平面标记，不假称找到了原NIF。
            data,mats,p=author_reticle.export(a,MATS);path=ROOT/'tools/source-cache/IrisReticle-Reference.png'
            put(A/('iris_fx_'+key+'.mesh'),data,'录像准星双层','两个分段环和四刻线、源录像红蓝色，薄平面无体积')
            assets.append({'key':key,'source':str(path),'sha256':a.sha(path),'materials':mats,'min':p.min(0).tolist(),'max':p.max(0).tolist(),'center':((p.max(0)+p.min(0))*.5).tolist(),'bound_radius':float(np.linalg.norm(p-(p.max(0)+p.min(0))*.5,axis=1).max()),'reference_reconstruction':True,'limitations':'准星按158.9秒录像重绘，未确认独立原NIF；平面随枪口轴向，不模拟相机HUD'})
            continue
        meshes,_=read_legacy(path) if key in ('beam','charge_halo','electro_burst') else a.read_nif(path)
        if key in ('shock','fire_blast'):meshes=fire_optics.flame_meshes(meshes)
        if key=='shell':meshes=fx_optics.canonical_disc(meshes,a)
        # 源anim首个辅助rod网格引用作者本机缺失贴图；只省去该辅助层，不猜色或替换正常武器。
        if key=='gun':meshes=[x for x in meshes if not any('vivianwitch' in t.lower() for t in x['textures'])]
        blocks={x['index']:x for x in nr.parse(path)['parsed_blocks']}
        # sequence拥有真正插值器，controller的NiBlend常量不是原关键帧。
        for seq in list(blocks.values()):
            for cb in seq.get('controlled_blocks',[]):
                if cb['controller'] in blocks:blocks[cb['controller']]['interpolator']=cb['interpolator']
        data,mats,p=mesh_bytes(meshes,blocks,(2.2,1.45) if key=='pulse_blast' else (1.35,1.15) if key=='shock' else (1,1.15) if key=='beam' else (1,1))
        if key in ('pulse_blast','shock','beam','exhaust','fire_blast','charge_halo','electro_burst'):
            seq='mIdle' if key in ('beam','charge_halo','electro_burst') else 'mSprayShort' if key=='exhaust' else 'SpecialIdle_AreaEffect'
            curves[key]=timeline(path,meshes,seq,a.C,a.SCALE)
            if key in ('shock','fire_blast'):meshes=fx_optics.ground_unit(meshes,curves[key],a);data,mats,p=mesh_bytes(meshes,blocks,(1.35,1.15))
            if key=='electro_burst':
                # 049与824范围层统一源长度单位；仅纵向仍接既有前20/R25终点，不改伤害球。
                meshes=normalize_beam(meshes,curves[key],True);factor=electro_area.beam_scale(sys.modules[__name__]);H=np.eye(4);H[:3,:3]=a.C*a.SCALE;B=np.diag([factor,factor,1,1]);Bi=np.linalg.inv(B)
                for mesh,tr in zip(meshes,curves[key]['tracks']):
                    mesh['matrix']=np.linalg.inv(H)@B@H@mesh['matrix']
                    for state in tr['frames']:
                        M=np.eye(4);M[:3]=np.asarray(state[13:]).reshape(3,4);M=B@M@Bi;state[13:]=M[:3].reshape(-1).tolist()
                old=np.asarray(curves[key]['bounds']);curves[key]['bounds']=(old*np.array([factor,factor,1])).tolist();curves[key]['source_xy_scale049']=factor
                data,mats,p=mesh_bytes(meshes,blocks)
            if key in ('beam','charge_halo'):meshes=normalize_beam(meshes,curves[key]);data,mats,p=mesh_bytes(meshes,blocks,(2.2,1.45) if key=='pulse_blast' else (1.35,1.15) if key=='shock' else (1,1.15) if key=='beam' else (1,1))
            if key=='beam':
                # 源五层管线的材质单独标记，不污染与其他招式共享的源材质。
                for name in mats:MATS[name]['beam_colour']=True
                data,mats,p=fx_optics.augment_beam(a,MATS,data,mats,p,curves[key])
            # Shader层内会旋转/扩散，保守包围盒必须同时包住整段源曲线，避免边缘被视锥错误裁掉。
            lo=np.minimum(p.min(0),curves[key]['bounds'][0]);hi=np.maximum(p.max(0),curves[key]['bounds'][1]);bound=max(float(np.linalg.norm(p,axis=1).max()),curves[key]['peak_radius'])
            data=data[:-34]+a.chunk(0x9000,struct.pack('<7f',*lo,*hi,bound))
        put(A/('iris_fx_'+key+'.mesh'),data,'八招源特效网格','源几何/法线/UV/RGBA，不生成廉价替代模型；源时间和透明采用独立明确适配')
        assets.append({'key':key,'source':str(path),'sha256':a.sha(path),'materials':mats,'min':p.min(0).tolist(),'max':p.max(0).tolist(),'center':((p.max(0)+p.min(0))*.5).tolist(),'bound_radius':float(np.linalg.norm(p-(p.max(0)+p.min(0))*.5,axis=1).max()),'limitations':'未运行完整NiPSys/屏幕折射/源程序闪电；shock/pulse_blast/beam/exhaust/fire_blast/charge_halo使用源曲线；火焰Glow绑定同源库羽化遮罩。光炮附加金环和电弧为用户参考图约束的三维重建，非源程序闪电；脉冲全层统一前向法线'})
    # 047同一源IrisBeam事件还有824范围爆发，与886光束分别消费，不复用地震火焰。
    area,curves['electro_area']=electro_area.build(sys.modules[__name__]);assets.append(area)
    finisher,curves['drill_blast']=drill_finisher.build(sys.modules[__name__]);assets.append(finisher)
    wings,curves['drill_wings']=iris_wings.build(sys.modules[__name__]);assets.append(wings)
    data,mats,p=fx_optics.ion_asset(a,MATS)
    put(A/'iris_fx_ion.mesh',data,'参考激发离子光','三维螺旋光丝、蓝白光谱、仅装饰；不冒称完整原NiPSys')
    ref=ROOT/'tools/source-cache/DriveIon-Reference.png'
    assets.append({'key':'ion','source':str(ref),'sha256':a.sha(ref),'materials':mats,'min':p.min(0).tolist(),'max':p.max(0).tolist(),'center':((p.max(0)+p.min(0))*.5).tolist(),'bound_radius':float(np.linalg.norm(p-(p.max(0)+p.min(0))*.5,axis=1).max()),'reference_reconstruction':True,'limitations':'按原视频激发瞬间重建，未完整执行原粒子系统'})
    for name,data in TEXTURES.items():put(A/name,data,'源贴图同像素PNG','从源mod或本机原版BSA逐项取原像素；BC7兼容转存，不改源档案')
    materials=[]
    for name,d in MATS.items():
        v=lambda x:' '.join('%.9f'%n for n in x)
        if 'energy_kind' in d:
            # 三维能量环/枪口离子层走独立程序，不读取虚构的原NIF纹理或控制器。
            materials.append('material '+name+'\n{\n technique { pass {\n lighting off\n depth_check on\n depth_write off\n cull_hardware none\n scene_blend src_alpha one\n vertex_program_ref IrisEnergyVP { param_named energyKind float4 '+str(d['energy_kind'])+' 0 0 0 }\n fragment_program_ref IrisEnergyFP { param_named_auto clock custom 1\n param_named energyKind float4 '+str(d['energy_kind'])+' 0 0 0 }\n } }\n}')
            continue
        if d.get('reference_reticle'):
            # 准星只显示录像轮廓和顶点红蓝色，不绑定球形噪声或日照材质。
            materials.append('material '+name+'\n{\n technique { pass {\n lighting off\n depth_check on\n depth_write off\n cull_hardware none\n scene_blend src_alpha one\n vertex_program_ref IrisEightVP {}\n fragment_program_ref IrisReticleFP { param_named_auto clock custom 1 }\n } }\n}')
            continue
        if d.get('wing_metal'):
            m=d['wing_metal']
            materials.append('material '+name+'\n{\n technique { pass {\n lighting off\n depth_check on\n depth_write on\n cull_hardware none\n scene_blend one zero\n vertex_program_ref IrisEightVP {}\n fragment_program_ref IrisWingMetalFP {\n param_named emission float3 '+v(d['emission'])+'\n param_named specularColour float3 '+v(m['specular'])+'\n param_named glossiness float '+str(m['glossiness'])+'\n param_named specularStrength float '+str(m['strength'])+'\n param_named uvTransform float4 '+v(d['uv'])+'\n }\n texture_unit { texture '+d['diffuse']+' }\n } }\n}\n')
            continue
        if d.get('burst_particle'):
            materials.append(drill_particles.material(name,d,TEXTURES));continue
        if d.get('particle'):
            materials.append('material '+name+'\n{\n technique { pass {\n lighting off\n depth_check on\n depth_write off\n cull_hardware none\n scene_blend src_alpha one_minus_src_alpha\n vertex_program_ref IrisQuakeVP {\n param_named_auto clock custom 1\n param_named atlas float4 '+v([d['atlas'],d['atlas'],d['atlas_fps'],d['atlas_frames']])+'\n param_named dustColour float4 '+v(d['rgb']+[d['alpha']])+'\n param_named dustFade float4 '+v([d['fade_in'],d['fade_out'],0,0])+'\n }\n fragment_program_ref IrisQuakeFP {}\n texture_unit { texture '+d['texture']+'\n tex_address_mode clamp\n }\n } }\n}')
            continue
        # 源火焰/火球多为src_alpha/one；统一alpha_blend会把黑底当遮挡，画成黑雾/黑球。
        materials.append('material '+name+'\n{\n technique { pass {\n lighting off\n depth_check on\n depth_write '+('on' if d['opaque'] else 'off')+'\n cull_hardware none\n scene_blend '+d['blend']+'\n vertex_program_ref '+('IrisBurstCardVP { param_named cardCenter float3 '+v(d['burst_card_center'])+' }' if 'burst_card_center' in d else 'IrisEightVP {}')+'\n fragment_program_ref IrisEightFP {\n param_named_auto clock custom 1\n param_named_auto sourceTint custom 2\n param_named_auto sourceUV custom 3\n param_named_auto sourceMisc custom 4\n param_named_auto sourceFalloff custom 8\n param_named uvBase float4 '+v(d['uv'])+'\n param_named uvFlow float4 '+v(d['scroll']+[0,0])+'\n param_named tint float4 '+v(d['emission']+[d['alpha']])+'\n param_named flags float4 '+v([int(d['effect']),int(d['opaque']),int(d['grey_color']),int(d['grey_alpha'])])+'\n param_named vertexFlags float4 '+v([int(d['vertex_color']),int(d['vertex_alpha']),int(d['use_falloff']),d['alpha_cutoff']])+'\n param_named effectParams float4 '+v([d['gain'],int(d['has_source']),int(d['has_palette']),0])+'\n param_named presentation float4 '+v(d.get('presentation',[1,1])+[int(d.get('beam_colour',False)),int(d.get('ion_blue',False))])+'\n param_named falloff float4 '+v(d['falloff'])+'\n }\n texture_unit { texture '+d['diffuse']+' }\n texture_unit { texture '+d['palette']+'\n tex_address_mode clamp\n }\n } }\n}')

    # 源金属像素阶段复用已实机验证的钻头算法，只适配当前VP的字段名；原生天空/地面/太阳仍自动绑定。
    import prepare_drill_optics
    metal=prepare_drill_optics.SHADER.split('float4 iris_drill_metal_fp(',1)[1].split('// 四张源弧光',1)[0]
    metal=('float4 iris_wing_metal_fp('+metal).replace('MetalOutput','VOut').replace('i.normal','i.n').replace('sourceTex.Sample(sourceSampler','t0.Sample(s0').replace('unitSafe','wingUnit')
    metal='float3 wingUnit(float3 x) {return x*rsqrt(max(dot(x,x),0.0000001));}\n'+metal
    # 独立有限爆炸程序只消费自有数据；不执行源物理或重用地震的贴地火焰。
    put(A/'iris_eight.hlsl',(SHADER+drill_particles.SHADER+muzzle_detail.shader(drill_particles.SHADER))+metal+TRAIL_FP+author_reticle.SHADER+fx_optics.SHADER,'八招源光学适配','源RGBA/梯度/UV流动/自发光，实例游戏时钟；不编译着色器')
    put(A/'iris_eight.program','vertex_program IrisEightVP hlsl\n{\n source iris_eight.hlsl\n entry_point iris_eight_vp\n target vs_4_0\n default_params {\n param_named_auto wvp worldviewproj_matrix\n param_named_auto normalMatrix inverse_transpose_world_matrix\n param_named_auto worldMatrix world_matrix\n param_named_auto cameraPosition camera_position\n param_named_auto clock custom 1\n param_named_auto delta0 custom 5\n param_named_auto delta1 custom 6\n param_named_auto delta2 custom 7\n }\n}\nfragment_program IrisEightFP hlsl\n{\n source iris_eight.hlsl\n entry_point iris_eight_fp\n target ps_4_0\n}\n','八招GPU程序声明','专用48字节顶点消费与custom1；无Renderable基类偏移')
    trail_texture=texture('textures/effects/GlowSlightFlash.dds');trail_palette=texture('textures/effects/gradients/GradFireCloak01.dds')
    materials.append('material IrisArsenal/Eight/WeaponTrail\n{\n technique { pass {\n lighting off\n depth_check on\n depth_write off\n cull_hardware none\n scene_blend src_alpha one\n vertex_program_ref IrisTrailVP {}\n fragment_program_ref IrisTrailFP {}\n texture_unit { texture '+trail_texture+' }\n texture_unit { texture '+trail_palette+' }\n } }\n}')
    # 两张图也由既有exhaust层引用，已经写入；不可偷偷引入未组包纹理。
    assert (A/trail_texture).exists() and (A/trail_palette).exists()
    put(A/'iris_eight.material','\n'.join(materials)+'\n','八招源材质','按源不同纹理和梯度分层，保留alpha并显式绑定本包纹理')
    put(A/'iris_eight.program',(A/'iris_eight.program').read_text('utf-8')+'vertex_program IrisTrailVP hlsl\n{\n source iris_eight.hlsl\n entry_point iris_trail_vp\n target vs_4_0\n default_params {\n param_named_auto wvp worldviewproj_matrix\n param_named_auto normalMatrix inverse_transpose_world_matrix\n param_named_auto worldMatrix world_matrix\n param_named_auto cameraPosition camera_position\n }\n}\nfragment_program IrisTrailFP hlsl\n{\n source iris_eight.hlsl\n entry_point iris_trail_fp\n target ps_4_0\n}\n','真实轨迹程序','沿用源火色梯度与实际历史alpha，不新增伤害')
    program=(A/'iris_eight.program').read_text('utf-8')+'fragment_program IrisReticleFP hlsl\n{\n source iris_eight.hlsl\n entry_point iris_reticle_fp\n target ps_4_0\n}\n'
    program+='vertex_program IrisEnergyVP hlsl\n{\n source iris_eight.hlsl\n entry_point iris_energy_vp\n target vs_4_0\n default_params {\n param_named_auto wvp worldviewproj_matrix\n param_named_auto normalMatrix inverse_transpose_world_matrix\n param_named_auto worldMatrix world_matrix\n param_named_auto cameraPosition camera_position\n param_named_auto clock custom 1\n }\n}\nfragment_program IrisEnergyFP hlsl\n{\n source iris_eight.hlsl\n entry_point iris_energy_fp\n target ps_4_0\n}\n'
    program+='fragment_program IrisWingMetalFP hlsl\n{\n source iris_eight.hlsl\n entry_point iris_wing_metal_fp\n target ps_4_0\n default_params {\n shared_params_ref SharedSkyParams\n shared_params_ref AmbientParams\n }\n}\n'
    put(A/'iris_eight.program',program+drill_particles.PROGRAM+muzzle_detail.PROGRAM,'平面准星程序','顶点红蓝色随游戏秒呼吸；不生成球体、不代编译')
    put(ROOT/'docs/eight-effects.json',json.dumps({'assets':assets,'textures':canonical_provenance(PROVENANCE,MATS),'materials':MATS,'not_ported':['beam.nif五层真实能量管网格/纹理已导出；三层BSProceduralLightningController为空网格，程序闪电未执行','EXDrill2已按AnimObjectA/B单骨精确导出；不是通用蒙皮运行时','完整NiPSys发射器和所有控制器尚未完整移植；地震按火焰变体源六层网格/曲线，准星按录像重绘','040终结保留ALS蓝相；火相为FullBust_End真实FireWave六曲面/七个ADDN64对象/两份MPS；枪口为ADDN09五源层；未执行完整NiPSys、受控重力、拖曳/湍流、程序闪电与屏幕折射' ],'optics034':{'pulse_disc_normal':'canonical +Z','quake_horizontal_radius':1,'beam_reference':str(ROOT/'tools/source-cache/DriveBeam-Reference.png'),'beam_reference_sha256':a.sha(ROOT/'tools/source-cache/DriveBeam-Reference.png'),'beam_source_layers':5,'beam_reference_ring_layers':1,'beam_reference_arc_layers':1,'ion':'reference reconstruction from159.8s; no original NiPSys runtime'},'optics036':{'finisher_opaque_shell_removed':True,'fire_roll_independent_source_curves':True,'fire_height_top_radius_ratio':.72,'source_charge3_layers':5,'source_trigger_clock':'effect_cues.csv','refractive_helpers_not_drawn':True},'quake':{'style':'fire','source':'SW/Iris/explosionwarm0.nif','reference_seconds':[215,217],'layers':6,'damage_events':4,'full_NiPSys':False},'timelines':{k:{a:b for a,b in v.items() if a!='tracks'} for k,v in curves.items()},'runtime_verified':False},ensure_ascii=False,indent=2),'八招特效来源与差异','逐层可查实际来源；未移植项公开列出，不宣称原版完全一致')
    track_rows=['IRIS_FX_CURVES 1 '+str(len(curves))]
    for key,d in curves.items():
        track_rows.append('%s %d %d %.9f %.9f'%(key,len(d['tracks']),d['samples'],d['duration'],d['peak_radius']))
        for tr in d['tracks']:
            track_rows.extend(' '.join('%.9f'%n for n in frame) for frame in tr['frames'])
    put(A/'effect_curves.csv','\n'.join(track_rows)+'\n','分层源光学时间流','每asset/子层30Hz颜色、UV、发光、衰减和增量变换；严格25数值有界，不按每发复制纹理')
    lines=['IRIS_FX 4 '+str(len(assets))]
    for x in assets:
        lines.append(x['key']+' iris_fx_'+x['key']+'.mesh '+str(len(x['materials']))+' '+ ' '.join('%.9f'%v for v in x['center']+[x['bound_radius']]))
        lines.extend(x['materials'])
    put(A/'effects.csv','\n'.join(lines)+'\n','运行时显式子材质绑定','每个自有实体逐SubEntity绑定，防止引擎工厂默认StaticObject覆盖源材质')
    # 059只在原十招资源完整生成后覆盖drive的beam/ion；UpdateMod删包重建也会执行同一作者。
    import drive_effects059
    drive_effects059.apply(sys.modules[__name__])
    # 063源枪口后处理最后执行，完整重建不会再覆盖回静态准星/错误脉冲准星。
    import muzzle_sources063
    muzzle_sources063.apply(sys.modules[__name__])
    # 064最后只重建钻天破源爆炸；其他招式保持各自作者输出，不影响日常Update。
    import finisher_sources064
    finisher_sources064.apply(sys.modules[__name__])
    # 067最后覆盖四条指定视觉记录；保留064爆炸、063枪口与066独立钻头材质流程。
    import source_effects067
    source_effects067.apply(sys.modules[__name__])
    # 068仅覆盖翻滚/钻天破/全力爆炸的源粒子语义；电脉与其他动作保持。
    import calibrate_bursts068
    calibrate_bursts068.apply(sys.modules[__name__])
    # 069私有源爆炸修正只消费068前驱；动态/配色修订在重建时保持，其他招式不串改。
    import source_burst069
    source_burst069.apply(sys.modules[__name__])
    # 073用户要求去掉翻滚内部深色火团；在源作者最后执行，重建不会恢复这两层。
    import roll_sphere073
    roll_sphere073.apply()
if __name__=='__main__':main()
