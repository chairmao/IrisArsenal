"""068仅校准翻滚/钻天破/全力爆炸的源粒子；独立VP避免串改其他招式。"""
# 070：移除已由AST与跨模块引用核实的未使用导入；原资源生产算法保持。
import copy,json,math
from types import SimpleNamespace
import numpy as np
from safeio import ROOT,put
from fx_timeline import raw_blocks
from nif_reader import Reader
from scene_geometry import chunks
from effect_data059 import curves
from drive_effects059 import mesh_blob,buffers_from_bytes
from finisher_sources064 import replace_sub
import drill_particles,fire_coverage
A=ROOT/'package/IrisArsenal/assets'
KEYS=('roll_blast','drill_blast','full_blast')


def source_models(a):
    """只取已有原NIF的完整尺寸键、角速度和源颜色；不修改共用导出器默认行为。"""
    models=[];previous=copy.deepcopy(a.MATS)
    for file in ('FireBallExp01.nif','MPSFireWaveFlames.nif'):
        path=ROOT/'tools/source-cache'/file;raw,strings=raw_blocks(path)
        layers,_=drill_particles.export(a,path,0,normalize=False)
        for l in layers:
            target=l['source_parameters']['target'];rotation=None;sizes=[];subtex=None
            for i,(kind,data) in raw.items():
                if kind not in ('NiPSysRotationModifier','BSPSysScaleModifier','BSPSysSubTexModifier'):continue
                r=Reader(data);r.read('II');t=r.read('I');active=r.read('B')
                if t!=target or not active:continue
                if kind=='NiPSysRotationModifier':
                    speed,var,angle,anglevar=r.read('4f');sign,random_axis=r.read('2B');axis=r.read('3f');r.done()
                    rotation=dict(speed=speed,variation=var,angle=angle,angle_variation=anglevar,random_sign=sign,random_axis=random_axis,axis=axis)
                elif kind=='BSPSysScaleModifier':
                    n=r.read('I');sizes=list(r.read(str(n)+'f'));r.done();assert 1<=n<=140
                else:subtex=list(r.read('7f'));r.done()
            d=copy.deepcopy(a.MATS[l['material']]);assert sizes
            models.append(dict(file=file,name=l['name'],texture=d['texture'],colors=d['colors'],sizes=sizes,rotation=rotation,subtex=subtex))
    a.MATS.clear();a.MATS.update(previous);return models


def match_model(d,models):
    return next((m for m in models if m['texture']==d.get('texture') and m['colors']==d.get('colors')),None)


def angular_speed(d,particles):
    # 独立确定性分布仅还原源范围/随机符号；不声称与Skyrim随机序列逐粒相同。
    r=d['rotation068'];p=np.asarray(particles);h=np.mod(np.sin(p[:,9]*12.9898+p[:,6]*78.233)*43758.5453,1)
    speed=r[0]+(h*2-1)*r[1]
    if r[2]>.5:speed*=np.where(h>.5,-1,1)
    return speed


def coverage(a,layers):
    """真实序列化粒子、完整尺寸曲线、修正后的淡出开始点；仍是软轮廓统计。"""
    # 共用旧量测器的纹理采样，但将淡出开始点转换为其旧的“持续比例”入参，仅此局部适配。
    mats=copy.deepcopy(a.MATS)
    for l in layers:mats[l['material']]['fade_out']=1-mats[l['material']]['fade_out']
    proxy=SimpleNamespace(MATS=mats,TEXTURES=a.TEXTURES)
    stop=max(p[6]+p[7] for l in layers for p in l['particles']);times=np.linspace(.015,stop-.005,36)
    bases=[];gold=math.pi*(3-math.sqrt(5));cache={};snaps=[]
    for n in range(12):
        y=1-2*(n+.5)/12;r=math.sqrt(1-y*y);f=np.array([r*math.cos(n*gold),y,r*math.sin(n*gold)]);right=np.cross(f,[0,1,0]);right/=np.linalg.norm(right);bases.append(np.stack([right,np.cross(right,f)]))
    for age in times:
        points=[];weights=[];power=0
        for l in layers:
            d=proxy.MATS[l['material']];rates=angular_speed(d,l['particles'])
            for j,p in enumerate(l['particles']):
                dt=age-p[6]
                if not 0<=dt<p[7]:continue
                uv,w=fire_coverage.samples(proxy,d,dt,p[7],cache)
                if not len(w):continue
                size=p[8]*np.interp(dt/p[7],np.linspace(0,1,len(d['sizes068'])),d['sizes068']);angle=p[9]+rates[j]*dt;cs,sn=math.cos(angle),math.sin(angle);xy=uv@np.array([[cs,sn],[-sn,cs]])*size
                center=np.array(p[:3])+np.array(p[3:6])*dt+.5*np.array(l['acceleration'])*dt*dt;points.append((center,xy));weights.append(w*size*size);power+=float(w.sum()*size*size)
        if power<=0:continue
        weight=np.concatenate(weights);radii=[]
        for base in bases:
            rr=np.concatenate([np.linalg.norm(xy+base@center,axis=1) for center,xy in points]);order=np.argsort(rr);ix=np.searchsorted(np.cumsum(weight[order]),weight.sum()*.95);radii.append(float(rr[order[min(ix,len(order)-1)]]))
        snaps.append(dict(age=float(age),radius95_by_view=radii,visible_area_proxy=power))
    assert snaps;return max(snaps,key=lambda x:x['visible_area_proxy'])


def vertex_shader():
    # 仅本轮三种爆炸引用；原IrisBurstVP、枪口/电脉等其他七招保持字节。
    s=drill_particles.SHADER.split('// 源NiBillboardNode')[0]
    s=s[s.index('VOut iris_burst_vp'):].replace('iris_burst_vp','iris_particle068_vp')
    extra=',uniform float4 rotationInfo,uniform float sourceSizeCount'+''.join(',uniform float4 sourceSize'+str(i) for i in range(35))
    s=s.replace('uniform float3 sourceAcceleration){','uniform float3 sourceAcceleration'+extra+'){')
    start=s.index(' float x=t*4;');end=s.index('\n float4 color=',start)
    values=','.join('sourceSize%d.%s'%(n//4,'xyzw'[n%4]) for n in range(140))
    s=s[:start]+' float sizes[140]={'+values+'};float x=t*max(0,sourceSizeCount-1);int low=min(138,(int)x);float size=lerp(sizes[low],sizes[low+1],saturate(x-low));'+s[end:]
    s=s.replace('(t-(1-fades.y))/max(.001,fades.y)','(t-fades.y)/max(.001,1-fades.y)').replace('t>1-fades.y?alphaOut','t>fades.y?alphaOut')
    s=s.replace('float cs=cos(i.c.w),sn=sin(i.c.w);','float hash=frac(sin(i.c.w*12.9898+i.c.x*78.233)*43758.5453);float speed=rotationInfo.x+(hash*2-1)*rotationInfo.y;if(rotationInfo.z>.5&&hash>.5)speed=-speed;float angle=i.c.w+speed*et;float cs=cos(angle),sn=sin(angle);')
    s=s.replace('uniform float4 sizeCurve,uniform float4 sizeEnd,','')
    return '// 068源淡出开始点、完整尺寸键与角速度；三处私有入口，无共享GPU状态修改。\nstruct VIn {float4 p:POSITION;float3 n:NORMAL;float4 c:COLOR;float2 uv:TEXCOORD0;};\nstruct VOut {float4 p:SV_Position;float4 c:COLOR;float2 uv:TEXCOORD0;float3 n:TEXCOORD1;float3 view:TEXCOORD2;};\n'+s


def material(name,d,textures):
    block=drill_particles.material(name,d,textures).replace('vertex_program_ref IrisBurstVP','vertex_program_ref IrisParticle068VP')
    lines=[line for line in block.splitlines() if 'param_named sizeCurve ' not in line and 'param_named sizeEnd ' not in line]
    at=next(i for i,l in enumerate(lines)if 'param_named sourceAcceleration ' in l)
    v=lambda x:' '.join('%.9f'%n for n in x)
    sizes=d['sizes068'];padded=sizes+[sizes[-1]]*(140-len(sizes));extra=[' param_named rotationInfo float4 '+v(d['rotation068']),' param_named sourceSizeCount float '+str(len(sizes))]
    extra+=[' param_named sourceSize%d float4 %s'%(n,v(padded[n*4:n*4+4]))for n in range(35)]
    lines[at:at]=extra;return '\n'.join(lines)+'\n'


def transform(a,base):
    # 纯数据变换供独立重放；base可指向任务快照。只处理三个既有效果，其他行逐字保留。
    doc=json.loads((base/'docs/eight-effects.json').read_text('utf8'));models=source_models(a);previous=copy.deepcopy(a.MATS);a.MATS.update(copy.deepcopy(doc['materials']))
    for spec in doc['materials'].values():
        for field in ('texture','diffuse','palette'):
            name=spec.get(field)
            if name and name not in a.TEXTURES:a.TEXTURES[name]=(A/name).read_bytes()
    proof=dict(clock_scope=['roll_blast','drill_blast','full_blast','vulcan_impact_blast','pulse_blast'],clock_exclusions=['shock','electro_area','beam','projectile_flight','attached_visuals'],contract='IRIS_BURST_CALIBRATION_068',alpha='FadeOutPercent is fade-start, not duration',detached_clock='game_seconds rate=1; spawn timing still native animation',scope=list(KEYS),particle_sort='unchanged birth-order; no shared IndexData or cross-thread GPU mutation added',subtex_limit='原图集仍按归一寿命取帧；源SubTex随机起帧/精确播放速率尚未移植，不伪称完整NiPSys',cases={})
    outputs={};updates={};newmats={}
    speeds={'roll_blast':doc['source067']['fireball']['speed'],'full_blast':doc['source067']['firewave']['speed'],'drill_blast':doc['finisher064']['timing']['fire_speed']}
    for key in KEYS:
        path=base/'package/IrisArsenal/assets'/('iris_fx_'+key+'.mesh');blob=path.read_bytes();parts=buffers_from_bytes(blob);states,duration,peak=curves(base/'package/IrisArsenal/assets/effect_curves.csv',key)
        assert not any('/Calibration068/' in name for name,rows in parts),'必须先生成064/067前驱，不能二次缩放068输出'
        raws=[blob[s-6:e]for kind,s0,e0 in chunks(blob,blob.index(b'\n')+1,len(blob))if kind==0x3000 for kind,s,e in chunks(blob,s0+1,e0)if kind==0x4000]
        layers=[];targets=[];names=[];source_notes=[]
        for i,(old,rr)in enumerate(parts):
            rows=rr.copy();d=copy.deepcopy(doc['materials'][old]);model=match_model(d,models) if d.get('burst_particle') else None
            is_fire=(('/Fire439C0/' in old or '/Fire6051F/' in old)if key=='roll_blast' else '/FireWave/'in old if key=='full_blast' else '/Fire/'in old)
            name='IrisArsenal/Calibration068/'+key+'/'+str(i);names.append(name)
            if model and is_fire:
                r=model['rotation'] or dict(speed=0,variation=0,random_sign=0);d.update(sizes068=model['sizes'],rotation068=[r['speed']*speeds[key],r['variation']*speeds[key],r['random_sign'],0],particle068=True)
                source_notes.append(dict(layer=i,source=model['file'],system=model['name'],sizes=len(model['sizes']),rotation=model['rotation'],subtex_unimplemented=model['subtex']))
                layers.append(dict(name=model['name'],material=name,particles=rows[::4,:10].tolist(),size_curve=d['sizes068'],acceleration=d.get('acceleration',[0,0,0])))
            elif d.get('burst_particle'):
                # 三处自有蓝相/暖冲击也消费同一源淡出字段；只更正开始点，已有尺寸/旋转近似保持。
                # 不读取别招材质，不把尚未核实的源力场或随机图集参数编造为已经移植。
                d.update(sizes068=d['size_curve'],rotation068=[0,0,0,0],particle068=True)
            a.MATS[name]=d;newmats[name]=d
            if is_fire:targets.append(i)
        body=[l for l in layers if l['name']=='pFireBall' if key=='roll_blast'] if key=='roll_blast' else [l for l in layers if l['name'].startswith('FlamesTall03')]
        assert body
        before=coverage(a,body);scale=1/min(before['radius95_by_view']);assert .5<scale<3,(key,scale)
        bound=peak
        for i,((old,rr),raw,name)in enumerate(zip(parts,raws,names)):
            rows=rr.copy();d=a.MATS[name]
            if i in targets:
                rows[:,:3]*=scale;states[i,:,[16,20,24]]*=scale
                if d.get('burst_particle'):
                    rows[:,3:6]*=scale;rows[:,8]*=scale;d['acceleration']=(np.array(d.get('acceleration',[0,0,0]))*scale).tolist()
                if 'burst_card_center'in d:d['burst_card_center']=(np.array(d['burst_card_center'])*scale).tolist()
            raws[i]=replace_sub(raw,old,name,rows)
            # 包围覆盖完整源尺寸键/路径；视角卡片采用旋转不变球包围，不能拿它反向缩小主体。
            if d.get('burst_particle'):
                sizes=d.get('sizes068',d['size_curve']);p=rows[::4];centers=p[:,:3]+p[:,3:6]*p[:,7,None]+.5*np.asarray(d.get('acceleration',[0,0,0]))*p[:,7,None]**2
                bound=max(bound,float(np.max(np.maximum(np.linalg.norm(p[:,:3],axis=1),np.linalg.norm(centers,axis=1))+p[:,8]*max(sizes)*math.sqrt(2))))
            else:
                for st in states[i]:
                    M=st[13:].reshape(3,4);q=rows[:,:3]@M[:,:3].T+M[:,3];bound=max(bound,float(np.linalg.norm(q,axis=1).max()))
            newmats[name]=d
        outputs[A/('iris_fx_'+key+'.mesh')]=mesh_blob(a.a,raws,[[-bound]*3,[bound]*3]);updates[key]=dict(names=names,states=states,duration=duration,peak=bound)
        asset=next(v for v in doc['assets']if v['key']==key);asset['materials']=names;asset.update(source_revision='068',center=[0,0,0],bound_radius=bound,min=[-bound]*3,max=[bound]*3);doc['timelines'][key]['peak_radius']=bound;doc['timelines'][key]['bounds']=[[-bound]*3,[bound]*3]
        proof['cases'][key]=dict(source=source_notes,before=before,uniform_fire_scale=scale,after_radius95=(np.array(before['radius95_by_view'])*scale).tolist(),radius={'roll_blast':24,'full_blast':90,'drill_blast':120}[key],duration=duration)
    # 材质名完整引号；旧共用声明/源纹理均不改。
    from drive_effects059 import shader_material
    text='// 068三处爆炸私有材质；保留源混合/像素，避免影响其他动作。\n'
    for name,d in newmats.items():
        if d.get('particle068'):block=material(name,d,a.TEXTURES)
        elif d.get('burst_particle'):block=drill_particles.material(name,d,a.TEXTURES)
        else:
            block=shader_material(name,d)
            if 'burst_card_center'in d:block=block.replace('IrisEightVP {}','IrisBurstCardVP { param_named cardCenter float3 '+' '.join('%.9f'%v for v in d['burst_card_center'])+' }')
        prefix='material '+name+'\n';assert block.startswith(prefix);text+='material "'+name+'"\n'+block[len(prefix):]
    outputs[A/'iris_particle068.material']=text
    outputs[A/'iris_particle068.hlsl']=vertex_shader()
    outputs[A/'iris_particle068.program']='''vertex_program IrisParticle068VP hlsl
{
 source iris_particle068.hlsl
 entry_point iris_particle068_vp
 target vs_4_0
 default_params {
 param_named_auto wvp worldviewproj_matrix
 param_named_auto inverseWorldView inverse_worldview_matrix
 param_named_auto clock custom 1
 }
}
'''
    lines=(base/'package/IrisArsenal/assets/effects.csv').read_text('utf8').splitlines();out=[lines[0]];i=1
    while i<len(lines):
        row=lines[i].split();end=i+1+int(row[2]);key=row[0]
        if key in updates:row[3:]=['0','0','0','%.9f'%updates[key]['peak']]
        out.append(' '.join(row) if key in updates else lines[i]);out.extend(updates[key]['names'] if key in updates else lines[i+1:end]);i=end
    outputs[A/'effects.csv']='\n'.join(out)+'\n'
    from muzzle_sources063 import take_curves,append_curve
    lines,count=take_curves((base/'package/IrisArsenal/assets/effect_curves.csv').read_text('utf8'),set(KEYS))
    for key,u in updates.items():append_curve(lines,key,dict(duration=u['duration'],samples=u['states'].shape[1],peak_radius=u['peak'],tracks=[dict(frames=frame.tolist())for frame in u['states']]))
    outputs[A/'effect_curves.csv']='IRIS_FX_CURVES 1 '+str(count+len(KEYS))+'\n'+'\n'.join(lines)+'\n'
    doc['materials'].update(newmats);doc['calibration068']=proof;outputs[ROOT/'docs/eight-effects.json']=json.dumps(doc,ensure_ascii=False,indent=2);outputs[ROOT/'docs/calibration068.json']=json.dumps(proof,ensure_ascii=False,indent=2)
    a.MATS.clear();a.MATS.update(previous);return outputs


def apply(a=None,base=ROOT):
    if a is None:import author_effects as a
    for p,data in transform(a,base).items():put(p,data,'068三处源粒子校准','独立VP修复淡出开始点/完整尺寸/角速度，统一火焰主体尺度；不改其他动作/伤害')
if __name__=='__main__':apply()
