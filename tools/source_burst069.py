"""069只校正翻滚/钻天破的实际源控制器与主体时序；不更改战斗或共用着色器。"""
# 070：移除已由AST与跨模块引用核实的未使用导入；原资源生产算法保持。
from pathlib import Path
import copy,json,math,re
import numpy as np
from safeio import ROOT,put
from fx_timeline import raw_blocks,timeline,sample as key_sample
from nif_reader import Reader,parse
from effect_data059 import curves
from drive_effects059 import buffers_from_bytes,mesh_blob,raw_sub,shader_material,sample
import drill_particles,calibrate_bursts068
A=ROOT/'package/IrisArsenal/assets'
KEYS=('roll_blast','drill_blast')
CONTRACT='IRIS_SOURCE_BURST_069'

def models(a):
    """读取目标系统的材质/寿命控制器；序列覆盖blend占位，未识别类型明确失败。"""
    paths=[(ROOT/'tools/source-cache/FireBallExp01.nif',False,None),
           (ROOT/'tools/source-cache/MPSFireWaveFlames.nif',False,None),
           (a.S/'Meshes/SW/Iris/ShoutAreaExplosionWarm0.nif',False,'SpecialIdle_AreaEffect'),
           (a.ELDEN/'meshes/ALS/ALSEXP.nif',False,'SpecialIdle_AreaEffect'),
           (a.ELDEN/'meshes/ALS/ALSshockEXP.nif',True,'mBegin'),
           (ROOT/'tools/source-cache/drive059/ShoutAreaExplosionSmall01.nif',False,'SpecialIdle_AreaEffect')]
    out=[];old=copy.deepcopy(a.MATS)
    for path,legacy,seqname in paths:
        raw,strings=raw_blocks(path);bs={b['index']:b for b in parse(path)['parsed_blocks']}
        seqs=[b for b in bs.values() if b['type']=='NiControllerSequence']
        seq=next((b for b in seqs if seqname is None or b['name']==seqname),None)
        layers,_=drill_particles.export(a,path,0,capacity_limit=512,normalize=False,legacy83=legacy,sequence_name=seqname)
        for l in layers:
            target=l['source_parameters']['target'];r=Reader(raw[target][1]);drill_particles.av(r,strings)
            if legacy:r.read('4i');r.read('B');shader,alpha=r.read('2i')
            else:r.read('4f');skin,shader,alpha=r.read('3i')
            fx=bs[shader];controls=[];life=None
            if seq:
                for c in seq['controlled_blocks']:
                    if c['node']!=l['name']:continue
                    if c['controller_type']=='NiPSysEmitterLifeSpanCtlr':life=bs[c['interpolator']]
                    if c['property']=='BSEffectShaderProperty':controls.append((bs[c['controller']],bs[c['interpolator']]))
            else:
                controls=[(b,bs[b['interpolator']]) for b in bs.values() if b['type'] in ('BSEffectShaderPropertyFloatController','BSEffectShaderPropertyColorController') and b['target']==shader and b['interpolator'] in bs]
            sizes=[];rot=None;subtex=[0,0,0,0,0,0,0]
            for _,(kind,data) in raw.items():
                if kind not in ('NiPSysRotationModifier','BSPSysScaleModifier','BSPSysSubTexModifier'):continue
                r=Reader(data);r.read('II');t=r.read('I');active=r.read('B')
                if t!=target or not active:continue
                if kind=='BSPSysSubTexModifier':subtex=list(r.read('7f'))
                elif kind=='BSPSysScaleModifier':n=r.read('I');sizes=list(r.read(str(n)+'f'))
                else:
                    speed,var,angle,anglevar=r.read('4f');sign,axisrandom=r.read('2B');axis=r.read('3f');rot=[speed,var,sign,0]
                r.done()
            out.append(dict(path=str(path),name=l['name'],target=target,shader=shader,fx=fx,blocks=bs,controls=controls,life=life,base_life=l['source_parameters']['life'],sizes=sizes or l['size_curve'],rotation=rot or [0,0,0,0],subtex=subtex,spec=copy.deepcopy(a.MATS[l['material']])))
    a.MATS.clear();a.MATS.update(old);return out

def property_state(model,t):
    """与原25浮点曲线一致：颜色、UV、增益、falloff、单位变换；不接触实体/物理。"""
    fx=model['fx'];c=list(fx['base_color']);uv=fx['uv_offset']+fx['uv_scale'];gain=fx['base_color_scale'];fall=list(fx['falloff'])
    for ctl,ip in model['controls']:
        age=t*ctl['frequency']+ctl['phase'];age=max(ctl['start'],min(ctl['stop'],age))
        value=key_sample(model['blocks'].get(ip.get('data'),{}),age,ip.get('constant',0));var=ctl['variable']
        if ctl['type']=='BSEffectShaderPropertyColorController' and var==0:c[:3]=np.asarray(value).tolist()
        elif ctl['type']=='BSEffectShaderPropertyFloatController':
            value=float(value)
            if var==0:gain=value
            elif var==5:c[3]=value
            elif var in (1,2,3,4):fall[var-1]=value
            elif var in (6,7,8,9):uv[{6:0,7:2,8:1,9:3}[var]]=value
    return np.array(c+uv+[gain]+fall+[1,0,0,0,0,1,0,0,0,0,1,0],float)

def shaders():
    # 保留068尺寸/旋转算法；只读原生vtable反汇编证明SubTex按寿命步数、随机起帧和循环，非固定FPS。
    vp=calibrate_bursts068.vertex_shader().replace('iris_particle068_vp','iris_particle069_vp')
    # Warm/Stokes确有150个尺寸键；068火焰专用上限140不足，私有入口扩到152，保留全部源键。
    vp=vp.replace('uniform float4 sourceSize34){','uniform float4 sourceSize34,uniform float4 sourceSize35,uniform float4 sourceSize36,uniform float4 sourceSize37){')
    vp=vp.replace('float sizes[140]','float sizes[152]').replace('sourceSize34.w};','sourceSize34.w,'+','.join('sourceSize%d.%s'%(n//4,'xyzw'[n%4]) for n in range(140,152))+'};').replace('min(138,(int)x)','min(150,(int)x)')
    vp=vp.replace('uniform float3 sourceAcceleration,','uniform float4 sourceUV,uniform float4 sourceClock,uniform float clockMode,uniform float4 atlasSequence,uniform float4 atlasSequence2,uniform float3 sourceAcceleration,')
    vp=vp.replace('// 矩形图集逐帧插值；半纹素内缩防止线性过滤混入相邻格，绝不把整张接触表铺在巨型面上。','// 源离散图集帧；半纹素内缩防止过滤混入相邻格。')
    vp=vp.replace('t>fades.y?alphaOut','fades.y>0&&t>fades.y?alphaOut')
    vp=vp.replace('float elapsed=clock.x-i.c.x','float elapsed=(clockMode>.5?sourceClock.w:clock.x)-i.c.x')
    start=vp.index(' float frame=t*max(0,atlas.z-1)');end=vp.index(' float2 local=',start)
    vp=vp[:start]+''' // 原生SubTex在第一次更新选择随机起帧，之后按floor(归一寿命*随机步数)前进并循环；不把同一格同步铺满整团。
 float h0=frac(sin(i.c.w*17.123+i.c.x*113.17+3.71)*41357.321),h1=frac(sin(i.c.w*91.713+i.c.x*21.17+9.3)*31519.579);
 float h2=frac(sin(i.c.w*37.931+i.c.x*45.11+2.7)*19517.147);
 float first=floor(atlasSequence.x+h0*atlasSequence.y),loopFirst=floor(atlasSequence.w+h2*atlasSequence2.x);
 float steps=floor(t*max(0,floor(atlasSequence2.y+h1*atlasSequence2.z)));
 float f0=first+steps;float loopCount=max(1,atlasSequence.z-loopFirst+1);
 if(f0>atlasSequence.z)f0=loopFirst+fmod(f0-atlasSequence.z-1,loopCount);
 f0=clamp(f0,0,max(0,atlas.z-1));float f1=f0;float frame=f0;float2 grid=max(float2(1,1),atlas.xy);
 float4 activeUV=clock.z>.5?sourceUV:uvBase;
'''+vp[end:]
    vp=vp.replace('uvBase.zw+uvBase.xy','activeUV.zw+activeUV.xy')
    fp='''
// 069独立像素入口。按源Effect着色器的灰度调色流程：alpha查表后即为结果，不再次乘寿命alpha。
Texture2D t0:register(t0);SamplerState s0:register(s0);Texture2D t1:register(t1);SamplerState s1:register(s1);
float4 iris_particle069_fp(VOut i,uniform float4 clock,uniform float4 sourceTint,uniform float4 sourceMisc,uniform float4 burstFlags,uniform float4 burstTint,uniform float4 propertyScale):SV_Target {
 clip(i.c.a-.00001);float4 texel=t0.Sample(s0,i.uv);float4 base=clock.z>.5?sourceTint:burstTint;
 float3 rgb=burstFlags.x>.5?t1.Sample(s1,saturate(float2(texel.g,i.c.r*base.r))).rgb:texel.rgb*i.c.rgb*base.rgb;
 float alpha=texel.a*i.c.a*base.a;
 if(burstFlags.y>.5)alpha=t1.Sample(s1,saturate(float2(texel.a,i.c.a*base.a))).a;
 float gain=clock.z>.5?sourceMisc.x*propertyScale.x:burstFlags.z;
 if(burstFlags.w>.5)rgb=dot(rgb,float3(.2126,.7152,.0722))*float3(.24,.60,1.6);
 // 明确的显示适配：仅非加法火球的冷却尾随原颜色键平滑透明；不改源贴图或制造橙色底板。
 if(propertyScale.y>.5){alpha*=smoothstep(0,.20,i.c.r*base.r);alpha*=smoothstep(.02,.16,dot(rgb*gain,float3(.2126,.7152,.0722)));}
 clip(alpha-.002);return float4(rgb*gain,saturate(alpha));
}
'''
    return vp+fp

def material(name,d,textures):
    s=calibrate_bursts068.material(name,d,textures).replace('IrisParticle068VP','IrisParticle069VP').replace('IrisBurstFP','IrisParticle069FP')
    v=lambda x:' '.join('%.9f'%float(t)for t in x)
    sub=d['subtex069'];s=s.replace(' param_named rotationInfo ',' param_named clockMode float '+str(d.get('clock_mode069',0))+'\n param_named rotationInfo ',1);s=s.replace(' param_named rotationInfo ', ' param_named atlasSequence float4 '+v(sub[:4])+'\n param_named atlasSequence2 float4 '+v(sub[4:]+[0])+'\n param_named rotationInfo ',1)
    # 只删参数表达式，保留同一行的程序闭括号；否则Ogre材质解析失败会导致插件全部招式停用。
    s=re.sub(r'param_named burstProfile float4(?: [-+.0-9eE]+){4}', '',s)
    sizes=d['sizes068'];assert 1<=len(sizes)<=152
    padded=sizes+[sizes[-1]]*(152-len(sizes))
    s=s.replace(' param_named sourceSizeCount ', ''.join(' param_named sourceSize%d float4 %s\n'%(i,v(padded[i*4:i*4+4]))for i in range(35,38))+' param_named sourceSizeCount ',1)
    return s.replace(' fragment_program_ref IrisParticle069FP {',' fragment_program_ref IrisParticle069FP {\n param_named_auto clock custom 1\n param_named_auto sourceTint custom 2\n param_named_auto sourceMisc custom 4\n param_named propertyScale float4 '+v([d['gain_ratio069'],d.get('cold069',0),0,0])+'\n')

def core_age(t,peak,end):
    # 参考视频白亮爆发先达到峰值，蓝相在0.52秒结束；对整个Stokes实例使用同一连续源时钟。
    # 不再用最晚火星寿命把主体峰值挤到0.055秒；出生/运动/颜色/几何同步消费本时钟。
    if t<=.20:return max(0,t)*peak/.20
    return min(end,peak+(t-.20)*(end-peak)/.32)


def transform(a,base):
    """纯变换：不写入，不修改源文件；可用冻结的068输入重复重放。"""
    doc=json.loads((base/'docs/eight-effects.json').read_text('utf8'));previous=copy.deepcopy(a.MATS);a.MATS.update(copy.deepcopy(doc['materials']));mods=models(a)
    for d in doc['materials'].values():
        for key in ('diffuse','texture','palette'):
            name=d.get(key)
            if name and name not in a.TEXTURES:a.TEXTURES[name]=(A/name).read_bytes()
    records=[];outputs={};updates={};newmats={};proof=dict(contract=CONTRACT,scope=list(KEYS),sources=records,source_frame_model='SkyrimSE.exe RTTI BSPSysSubTexModifier update 0xD64BF0; random start + lifetime step count + loop; discrete frame',source_color_model='SkyrimSE.exe BSPSysSimpleColorModifier 0x1323550; zero fade-out holds alpha; independent RGB/alpha',particle_sort='既有出生顺序保持；未增加共享缓冲写入/线程',unresolved='ADDN334在349个本机mod插件中仍无定义；ALSshock的mBegin中Lightning04可见性为false，不能擅自添加常亮闪电；折射和原ENB未移植',cases={})
    core_path=ROOT/'tools/source-cache/drive059/ShoutAreaExplosionSmall01.nif'
    from finisher_coverage064 import measure
    cm,_=a.a.read_nif(core_path);cm=[m for m in cm if not __import__('fire_optics').refractive(m)]
    cd=timeline(core_path,cm,'SpecialIdle_AreaEffect',a.a.C,a.a.SCALE);cb={b['index']:b for b in parse(core_path)['parsed_blocks']}
    core_measure=measure(a,cm,cd['tracks'],cb,cd['duration'],min(cd['duration'],1.666666746))
    core_factor=1/min(core_measure['radius95_by_view']);core_ratio=core_factor/doc['finisher064']['stokes_uniform_scale']
    core_peak=core_measure['age'];core_end=doc['finisher064']['stokes_time_scale']*.52
    proof['stokes']={'measure':core_measure,'uniform_scale_ratio':core_ratio,'source_peak':core_peak,'source_end':core_end,'mapped_peak':.20,'mapped_end':.52}
    proof['flight_excluded']=['ALS/ALSPRO.nif为实体飞矛','RuneMagic/RedDragonrendprojectile.nif与MoonProjhorzV1.nif为飞行阶段；不冻结为爆炸','Iris8D9 PlasmaBall.nif未由该MGEF引用；不能因为文件存在就接入']
    proof['reference_exposure_adapter']=doc['source067']['warm']['display_exposure_adapter']
    proof['cold_opacity_adapter']='仅翻滚普通alpha火球：温度色键0..0.20和线性亮度0.02..0.16平滑衰减冷却尾/极暗像素遮挡；原序列图/LUT/曝光保持，用户明确要求不要太黑色块'
    for key in KEYS:
        blob=(base/'package/IrisArsenal/assets'/('iris_fx_'+key+'.mesh')).read_bytes();parts=buffers_from_bytes(blob);states,duration,peak=curves(base/'package/IrisArsenal/assets/effect_curves.csv',key);items=[];notes=[]
        for i,(old,rr) in enumerate(parts):
            rows=rr.copy();d=copy.deepcopy(doc['materials'][old]);frames=states[i].copy();speed=1.;delay=0.
            assert old.startswith('IrisArsenal/Calibration068/'+key+'/'),'必须消费068前驱，不能二次缩放069'
            # 同一星火纹理/颜色被多个NIF复用，不能仅凭纹理选第一个；使用已确认068层来源并再次核对像素合同。
            source_name=({3:'ShoutAreaExplosionWarm0.nif',6:'FireBallExp01.nif',7:'FireBallExp01.nif',10:'FireBallExp01.nif',11:'FireBallExp01.nif'} if key=='roll_blast' else {16:'ALSEXP.nif',17:'ALSshockEXP.nif',18:'ALSshockEXP.nif',19:'ShoutAreaExplosionSmall01.nif',26:'MPSFireWaveFlames.nif',27:'MPSFireWaveFlames.nif'}).get(i)
            candidates=[m for m in mods if Path(m['path']).name.casefold()==str(source_name).casefold() and m['spec']['texture']==d.get('texture') and m['spec']['colors']==d.get('colors')]
            model=None
            if d.get('burst_particle'):
                assert len(candidates)==1,(key,i,source_name,len(candidates));model=candidates[0]
            if model:
                if key=='roll_blast':speed=doc['source067']['fireball']['speed']if 'FireBall' in model['path']else doc['source067']['warm']['speed'];delay=.1 if i>=8 else 0.
                elif 'MPSFireWave' in model['path']:speed=doc['finisher064']['timing']['fire_speed'];delay=doc['finisher064']['timing']['fire_begin']
                elif 'ShoutAreaExplosionSmall' in model['path']:speed=doc['finisher064']['stokes_time_scale']
                if model['life']:
                    ip=model['life'];original_birth=(rows[:,6]-delay)*speed
                    for j,t in enumerate(original_birth):rows[j,7]+=float(key_sample(model['blocks'].get(ip.get('data'),{}),float(t),model['base_life'])-model['base_life'])/speed
                    assert np.min(rows[:,7])>0
                d['cold069']=1 if key=='roll_blast' and model['name']=='pFireBall' else 0
                d.update(particle069=True,source069=model['path'],system069=model['name'],sizes068=model['sizes'],rotation068=[model['rotation'][0]*speed,model['rotation'][1]*speed,model['rotation'][2],0],subtex069=model['subtex'],gain_ratio069=d['gain']/model['fx']['base_color_scale'])
                is_core=key=='drill_blast' and 'ShoutAreaExplosionSmall' in model['path']
                d['clock_mode069']=int(is_core)
                if is_core:
                    rows[:,3:6]/=speed;rows[:,6:8]*=speed
                    d['acceleration']=(np.asarray(d.get('acceleration',[0,0,0]))/speed**2).tolist()
                    d['rotation068']=model['rotation'][:]
                    rows[:,:3]*=core_ratio;rows[:,3:6]*=core_ratio;rows[:,8]*=core_ratio;d['acceleration']=(np.asarray(d['acceleration'])*core_ratio).tolist()
                    def state_fn(t,m=model):
                        age=core_age(t,core_peak,core_end);st=property_state(m,age);st[16]=age;return st
                else:
                    def state_fn(t,m=model,rate=speed,begin=delay):return property_state(m,max(0,t-begin)*rate)

                duration=max(duration,float(np.max(rows[:,6]+rows[:,7]))) if not is_core else duration;notes.append(dict(layer=i,source=model['path'],system=model['name'],property_controllers=len(model['controls']),life_controller=model['life']is not None,subtex=model['subtex'],speed=speed,delay=delay))
            else:
                if key=='drill_blast' and i in (3,4,5):
                    # 直接从对应原NIF轨道取样，避免再插值已经7倍压缩的稀疏064数据。
                    rows[:,:3]*=core_ratio
                    source_frames=np.asarray(cd['tracks'][i-3]['frames'])
                    def state_fn(t,frames=source_frames,dur=cd['duration']):
                        st=sample(frames,core_age(t,core_peak,core_end),dur).copy();st[[16,20,24]]*=core_factor
                        if t>=.52:st[3]=0
                        return st
                else:
                    def state_fn(t,frames=frames,dur=duration):return sample(frames,t,dur).copy()

            # 原网格三角从源已确认的严格消费者读取，不以顶点数猜拓扑。
            from scene_geometry import mesh
            items.append(dict(rows=rows,tri=mesh(base/'package/IrisArsenal/assets'/('iris_fx_'+key+'.mesh'))[i]['tri'],spec=d,frame=state_fn,original=i))
        assert len(items)<=32
        count=min(241,math.ceil(duration*60)+1);times=np.linspace(0,duration,count);tracks=[];raws=[];names=[];bound=peak
        for i,item in enumerate(items):
            name='IrisArsenal/Source069/'+key+'/'+str(i);d=item['spec'];rows=item['rows'];frames=np.asarray([item['frame'](float(t))for t in times]);assert frames.shape==(count,25)and np.isfinite(frames).all()
            newmats[name]=d;names.append(name);tracks.append(dict(frames=frames.tolist()));raws.append(raw_sub(a.a,name,rows,item['tri']))
            if d.get('burst_particle'):
                p=rows[::4];life=p[:,7,None];centers=p[:,:3]+p[:,3:6]*life+.5*np.asarray(d.get('acceleration',[0,0,0]))*life**2
                bound=max(bound,float(np.max(np.maximum(np.linalg.norm(p[:,:3],axis=1),np.linalg.norm(centers,axis=1))+p[:,8]*max(d.get('sizes068',d['size_curve']))*math.sqrt(2))))
            else:
                for st in frames:
                    mat=st[13:].reshape(3,4);bound=max(bound,float(np.linalg.norm(rows[:,:3]@mat[:,:3].T+mat[:,3],axis=1).max()))
        outputs[A/('iris_fx_'+key+'.mesh')]=mesh_blob(a.a,raws,[[-bound]*3,[bound]*3]);updates[key]=dict(names=names,duration=duration,samples=count,peak_radius=bound,tracks=tracks,bounds=[[-bound]*3,[bound]*3])
        asset=next(x for x in doc['assets']if x['key']==key);asset.update(materials=names,source_revision='069',center=[0,0,0],bound_radius=bound,min=[-bound]*3,max=[bound]*3);doc['timelines'][key]={k:v for k,v in updates[key].items()if k not in ['names','tracks']};proof['cases'][key]=dict(layers=len(items),duration=duration,particles=notes,radius={'roll_blast':24,'drill_blast':120}[key])
    text='// 069只用于翻滚/钻天破；源控制器和源混合保持，未替换其他招式材质。\n'
    for name,d in newmats.items():
        if d.get('particle069'):block=material(name,d,a.TEXTURES)
        else:
            block=shader_material(name,d)
            if 'burst_card_center'in d:block=block.replace('IrisEightVP {}','IrisBurstCardVP { param_named cardCenter float3 '+' '.join('%.9f'%v for v in d['burst_card_center'])+' }')
        prefix='material '+name+'\n';assert block.startswith(prefix);text+='material "'+name+'"\n'+block[len(prefix):]
    outputs[A/'iris_source069.material']=text;outputs[A/'iris_source069.hlsl']=shaders();outputs[A/'iris_source069.program']='''vertex_program IrisParticle069VP hlsl
{ source iris_source069.hlsl
 entry_point iris_particle069_vp
 target vs_4_0
 default_params {
 param_named_auto wvp worldviewproj_matrix
 param_named_auto inverseWorldView inverse_worldview_matrix
 param_named_auto clock custom 1
 param_named_auto sourceUV custom 3
 param_named_auto sourceClock custom 5
 } }
fragment_program IrisParticle069FP hlsl
{ source iris_source069.hlsl
 entry_point iris_particle069_fp
 target ps_4_0
}
'''
    for name,data in a.TEXTURES.items():
        if not (A/name).exists():outputs[A/name]=data
    lines=(base/'package/IrisArsenal/assets/effects.csv').read_text('utf8').splitlines();out=[lines[0]];i=1
    while i<len(lines):
        row=lines[i].split();end=i+1+int(row[2]);key=row[0]
        if key in updates:
            u=updates[key];out.append(key+' iris_fx_'+key+'.mesh '+str(len(u['names']))+' 0 0 0 %.9f'%u['peak_radius']);out.extend(u['names'])
        else:out.extend(lines[i:end])
        i=end
    outputs[A/'effects.csv']='\n'.join(out)+'\n'
    from muzzle_sources063 import take_curves,append_curve
    lines,count=take_curves((base/'package/IrisArsenal/assets/effect_curves.csv').read_text('utf8'),set(KEYS))
    for key,u in updates.items():append_curve(lines,key,u)
    outputs[A/'effect_curves.csv']='IRIS_FX_CURVES 1 '+str(count+len(KEYS))+'\n'+'\n'.join(lines)+'\n'
    doc['materials'].update(newmats);doc['source069']=proof;outputs[ROOT/'docs/eight-effects.json']=json.dumps(doc,ensure_ascii=False,indent=2);outputs[ROOT/'docs/source-burst069.json']=json.dumps(proof,ensure_ascii=False,indent=2)
    a.MATS.clear();a.MATS.update(previous);return outputs,proof

def apply(a=None):
    if a is None:import author_effects as a
    outputs,_=transform(a,ROOT)
    for path,data in outputs.items():put(path,data,'069独立源爆炸修正','源控制器/SubTex/遗漏分支；其他八招、战斗、DLL不改')
if __name__=='__main__':apply()
