"""064钻天破终结：真实ALS源爆发与遗漏ALSshock粒子，随后原FireWave；无自造覆盖球。"""
# 070：移除已由AST与跨模块引用核实的未使用导入；原资源生产算法保持。
import copy,json,struct
import numpy as np
from safeio import ROOT,put
from fx_timeline import timeline
from drive_effects059 import raw_sub,mesh_blob,shader_material,sample
from drill_finisher import billboard_names
import drill_particles,fire_burst,fire_coverage
A=ROOT/'package/IrisArsenal/assets'
IDENT=fire_burst.IDENTITY
BLUE_END=.52
FIRE_BEGIN=.56
FIRE_SPEED=2.

def scaled_layers(a,layers,factor):
    for layer in layers:
        old=layer['material'];name='IrisArsenal/Finisher064/'+old.split('DrillBurst/')[-1]
        a.MATS[name]=copy.deepcopy(a.MATS[old]);layer['material']=name
        # 电离着色沿用项目已确认的蓝色显示适配；保留原贴图、渐变、RGBA与相对空间。
        layer['acceleration']=(np.asarray(layer.get('acceleration',[0,0,0]))*factor).tolist()
        a.MATS[name]['acceleration']=layer['acceleration']
        for p in layer['particles']:
            for k in range(6):p[k]*=factor
            p[8]*=factor

def build(a):
    blue=a.ELDEN/'meshes/ALS/ALSEXP.nif';shock=a.ELDEN/'meshes/ALS/ALSshockEXP.nif'
    meshes,_=a.a.read_nif(blue);assert len(meshes)==3
    d=timeline(blue,meshes,'SpecialIdle_AreaEffect',a.a.C,a.a.SCALE)
    blocks={b['index']:b for b in a.nr.parse(blue)['parsed_blocks']};cards=billboard_names(blue)
    # 8D5 -> 0B55 ALSExp -> placed EXPL0B54 ALSshock；mBegin是真实起爆序列，不能误取mEnd。
    sparks,record1=drill_particles.export(a,blue,0,BLUE_END,normalize=False)
    shock_layers,record2=drill_particles.export(a,shock,0,BLUE_END,sequence_name='mBegin',legacy83=True,normalize=False)
    # 名为AddOnNode33的节点实际值334；当前主文件未找到ADDN334，不能误接原版33。
    # CAST8D4的Stokes链则可确认：0B0B脚本 -> 0B0A -> MGEF0AF4 -> EXPL0AF3。
    core=ROOT/'tools/source-cache/drive059/ShoutAreaExplosionSmall01.nif'
    import fire_optics
    cm,_=a.a.read_nif(core);cm=[m for m in cm if not fire_optics.refractive(m)]
    cd=timeline(core,cm,'SpecialIdle_AreaEffect',a.a.C,a.a.SCALE)
    core_layers,record3=drill_particles.export(a,core,0,capacity_limit=512,normalize=False)
    # 证据保留变换前的源粒子值；下面的时间/空间适配不能反写到原始记录。
    record1=copy.deepcopy(record1);record2=copy.deepcopy(record2);record3=copy.deepcopy(record3)
    layers=sparks+shock_layers
    # 用实际图集/LUT的alpha面积测量源粒子主体，不以透明边角或火星最远点压缩爆炸主体。
    # 所有ALS层只接受同一个相似缩放；不再单独把冲击环撑到R120或另造49个球形雾片。
    for layer in layers:a.MATS[layer['material']]['ion_blue']=True
    coverage=fire_coverage.measure(a,layers,np.linspace(.02,.49,22));reference=max(coverage['radius95_by_view']);assert reference>0
    # ALS闪光的透明边缘和电纹仍有真实空间尺寸；联合源几何包络，避免少量大电纹超出R120数倍。
    for mesh,tr in zip(meshes,d['tracks']):
        p=(np.asarray(mesh['vertices'])@mesh['matrix'][:3,:3].T+mesh['matrix'][:3,3])@a.a.C.T*a.a.SCALE
        for ti in np.linspace(.02,BLUE_END,25):
            st=sample(np.asarray(tr['frames']),ti,d['duration']);M=st[13:].reshape(3,4)
            if st[3]>.05 and max(st[:3])>.02:reference=max(reference,float(np.linalg.norm(p@M[:,:3].T+M[:,3],axis=1).max()))
    factor=1/reference;scaled_layers(a,layers,factor)
    # 同一招原本分别施放ALS与Stokes两套完整效果；每套内部只作统一相似缩放。
    # Stokes用源可见阶段的几何包络标定到既有R120，不能给每片网格独立撑大。
    core_peak=0
    for mesh,tr in zip(cm,cd['tracks']):
        p=(np.asarray(mesh['vertices'])@mesh['matrix'][:3,:3].T+mesh['matrix'][:3,3])@a.a.C.T*a.a.SCALE
        for ti in np.linspace(.02,cd['duration'],60):
            st=sample(np.asarray(tr['frames']),ti,cd['duration']);M=st[13:].reshape(3,4)
            if st[3]>.05:core_peak=max(core_peak,float(np.linalg.norm(p@M[:,:3].T+M[:,3],axis=1).max()))
    core_coverage=fire_coverage.measure(a,core_layers,np.linspace(.02,record3['life']-.02,32))
    core_peak=max(core_peak,max(core_coverage['radius95_by_view']));assert core_peak>0
    core_factor=1/core_peak;scaled_layers(a,core_layers,core_factor)
    # 不能只把2.5秒寿命截成0.52秒而保留慢速度：整套源运动按同一时间比例压缩，路径形状保持。
    core_speed=record3['life']/BLUE_END
    for layer in core_layers:
        for p in layer['particles']:p[3:6]=(np.asarray(p[3:6])*core_speed).tolist();p[6]/=core_speed;p[7]/=core_speed
        layer['acceleration']=(np.asarray(layer.get('acceleration',[0,0,0]))*core_speed**2).tolist()
        spec=a.MATS[layer['material']];spec['acceleration']=layer['acceleration'];spec['ion_blue']=True
    # 参考视频含ENB曝光；只为这套源冲击作公开的显示曝光适配，不改源纹理/颜色键或其他招式。
    core_exposure=4.
    for layer in core_layers:a.MATS[layer['material']]['gain']*=core_exposure
    # 同一CAST8D4的0AFB/0AF8 -> PROJ0AF7明确引用DragonRendProjectile。
    # 这里只移植其原五层蓝色曲面到共同球心作视觉，不创建/移动投射物，也不改球形伤害。
    wave=ROOT/'tools/source-cache/DragonRendProjectile.nif'
    wm,_=a.a.read_nif(wave);wm=[m for m in wm if not fire_optics.refractive(m)]
    wd=timeline(wave,wm,None,a.a.C,a.a.SCALE);assert len(wm)==5
    wave_areas=np.zeros(wd['samples']);wave_radius=0
    for mesh,tr in zip(wm,wd['tracks']):
        p=(np.asarray(mesh['vertices'])@mesh['matrix'][:3,:3].T+mesh['matrix'][:3,3])@a.a.C.T*a.a.SCALE;tri=np.asarray(mesh['triangles'])
        for i,st in enumerate(np.asarray(tr['frames'])):
            M=st[13:].reshape(3,4);q=p@M[:,:3].T+M[:,3];energy=st[3]*max(st[:3])*st[8]
            area=np.linalg.norm(np.cross(q[tri[:,1]]-q[tri[:,0]],q[tri[:,2]]-q[tri[:,0]]),axis=1).sum()*.5
            wave_areas[i]+=area*energy
            if energy>.1:wave_radius=max(wave_radius,float(np.linalg.norm(q,axis=1).max()))
    assert wave_radius>0
    # 包围含大片零alpha边角，直接用最远顶点会把可见蓝流压成小光点。
    # 改用真实RGBA/LUT、源alpha/falloff和三角投影面积的十二视角测量，整套源曲面统一缩放。
    import finisher_coverage064
    wave_blocks={b['index']:b for b in a.nr.parse(wave)['parsed_blocks']}
    wave_coverage=finisher_coverage064.measure(a,wm,wd['tracks'],wave_blocks,wd['duration'],1.666666746)
    wave_scale=1/min(wave_coverage['radius95_by_view']);wave_peak_age=wave_coverage['age']
    wave_speed=max(1.,wave_peak_age/.20)
    # 原版蓝流原为高速移动投射物，后半段不断扩张；用户本次要固定球心的R120爆炸。
    # 只给整个源实例施加同一连续相似缩放，使可见主体不超过4R/3；火相至少R，保持旧3/4要求。
    # 不逐层改形状，不改UV/颜色/相对比例，也不增添空间散布的自造贴图。
    wave_cap=4./3.;wave_times=[x['age']for x in wave_coverage['time_series']]
    wave_radii=[max(x['radius95_by_view'])for x in wave_coverage['time_series']]
    wave_peak_cap=min(1.,wave_cap/(max(wave_coverage['radius95_by_view'])*wave_scale))
    # 火相与源3F9ED调用一致；六曲面与七处附加发射器保持完整相对空间，不借地震。
    fire=fire_burst.components(a,0,None)
    body=[l for l in fire['record']['layers'] if l['name'].startswith('FlamesTall03')]
    fire_measure=fire_coverage.measure(a,body,np.linspace(.05,fire['duration']-.05,40))
    # 用户最新要求覆盖整个R120，不再沿用旧3/4标准。十二方向都至少覆盖单位球半径1。
    fire_scale=1/min(fire_measure['radius95_by_view']);assert 0<fire_scale<16
    # 录像240.6起火、约240.8达到主体峰值；以实测源峰值时刻映射0.20秒，不删源层或重排粒子。
    fire_speed=max(FIRE_SPEED,fire_measure['age']/.20)
    duration=FIRE_BEGIN+fire['duration']/fire_speed;samples=round(duration*30)+1;assert samples<=241
    times=np.linspace(0,duration,samples);subs=[];tracks=[];names=[];positions=[];cull=[]
    sources=[(blue,mesh,tr,d,blocks,factor) for mesh,tr in zip(meshes,d['tracks'])]
    cb={b['index']:b for b in a.nr.parse(core)['parsed_blocks']}
    sources.extend((core,mesh,tr,cd,cb,core_factor) for mesh,tr in zip(cm,cd['tracks']))
    wb={b['index']:b for b in a.nr.parse(wave)['parsed_blocks']}
    # Stokes的两条实际脚本分支分别发射PROJ0AF7/0AFD，二者都引用这份原NIF。
    # 保留两份源可视实例的重叠透明混合；只复制视觉，不生成第二次伤害或投射物。
    sources.extend((wave,mesh,tr,wd,wb,wave_scale) for _ in range(2) for mesh,tr in zip(wm,wd['tracks']))
    occurrences={}
    for source,mesh,tr,td,source_blocks,scale in sources:
        # 保留源无纹理闪光的顶点alpha羽化，不擅自补GlowSlightFlash遮罩。
        blob,mats,p=a.mesh_bytes([mesh],source_blocks);old=mats[0];key=(str(source),mesh['index']);occurrences[key]=occurrences.get(key,0)+1
        name='IrisArsenal/Finisher064/'+source.stem+'/'+mesh['name']+('/PROJ0AFD'if source==wave and occurrences[key]>1 else '')
        spec=copy.deepcopy(a.MATS[old]);spec['ion_blue']=True
        if source==core:spec['presentation']=[1.,core_exposure]
        rows=buffers_from_blob(blob)[0][1].copy();rows[:,:3]*=scale;p=rows[:,:3]
        if mesh['name'] in cards:spec['burst_card_center']=((p.min(0)+p.max(0))*.5).tolist()
        a.MATS[name]=spec;frames=[]
        for t in times:
            st=sample(np.asarray(tr['frames']),float(t)*(core_speed if source==core else wave_speed if source==wave else 1.),td['duration']).copy()
            for k in (16,20,24):st[k]*=scale
            if source==wave:
                source_age=float(t)*wave_speed;visible_radius=float(np.interp(source_age,wave_times,wave_radii))*wave_scale
                cap=min(1.,wave_cap/max(1e-6,visible_radius));st[13:]*=cap
            # 保持源最初0.52秒的快速膨胀和闪白，不把整段长尾挤成一帧；火相另走独立已加速的时间。
            if t>=BLUE_END:st[3]=0
            frames.append(st.tolist());mat=st[13:].reshape(3,4);cull.extend(p@mat[:,:3].T+mat[:,3])
        subs.append(raw_sub(a.a,name,rows,mesh['triangles']));names.append(name);positions.extend(p);tracks.append({'mesh':mesh['name'],'frames':frames})
    for layer in layers+core_layers:
        sub,p=drill_particles.submesh(a,layer);subs.append(sub);names.append(layer['material']);positions.extend(p);tracks.append({'mesh':layer['name'],'frames':[IDENT[:] for _ in times]})
    # 原火焰的加速演出已经在顶点出生/速度/寿命及轨道中统一烘焙，运行时不再依赖“前5层”的脆弱索引。
    raw=mesh_blob(a.a,fire['subs'],fire['bounds']);parts=buffers_from_blob(raw)
    # 原组件顺序固定为六片曲面+两个合批粒子池，直接读取原子块索引而不是重建或增发粒子。
    for index,((old,rows),tr) in enumerate(zip(parts,fire['tracks'])):
        name='IrisArsenal/Finisher064/Fire/'+str(index);spec=copy.deepcopy(a.MATS[old]);rows=rows.copy();rows[:,:3]*=fire_scale
        if spec.get('burst_particle'):
            rows[:,3:6]*=fire_scale*fire_speed;rows[:,6]=FIRE_BEGIN+rows[:,6]/fire_speed;rows[:,7]/=fire_speed;rows[:,8]*=fire_scale
            spec['acceleration']=(np.asarray(spec.get('acceleration',[0,0,0]))*fire_scale*fire_speed**2).tolist()
        a.MATS[name]=spec;frames=[]
        for t in times:
            age=(float(t)-FIRE_BEGIN)*fire_speed;st=sample(np.asarray(tr['frames']),max(0,age),fire['duration']).copy()
            for k in (16,20,24):st[k]*=fire_scale
            if age<0 or age>=fire['duration']:st[3]=0
            frames.append(st.tolist());m=st[13:].reshape(3,4);cull.extend(rows[:,:3]@m[:,:3].T+m[:,3])
        sub=replace_sub(fire['subs'][index],old,name,rows);subs.append(sub);names.append(name);positions.extend(rows[:,:3]);tracks.append({'mesh':tr['mesh'],'frames':frames})
    positions=np.asarray(positions);cull.extend(fire_burst.part_bounds(layers+core_layers));cull.extend(np.asarray(fire['bounds'])*fire_scale)
    bound=float(np.linalg.norm(np.asarray(cull),axis=1).max());assert np.isfinite(bound)
    # 所有相机朝向卡片用旋转不变的保守球包围；该球仅用于裁剪，绝不作为伤害/显示尺度分母。
    blob=mesh_blob(a.a,subs,[[-bound]*3,[bound]*3]);put(A/'iris_fx_drill_blast.mesh',blob,'064源终结网格','源ALS三层/59火花、ALSshock真实mBegin、Stokes三曲面/275粒子、DragonRend五曲面蓝流和原FireWave；删除自造49片覆盖球')
    center=(positions.min(0)+positions.max(0))*.5
    asset={'key':'drill_blast','source':str(blue),'sha256':a.a.sha(blue),'materials':names,'min':positions.min(0).tolist(),'max':positions.max(0).tolist(),'center':center.tolist(),'bound_radius':float(np.linalg.norm(positions-center,axis=1).max()),'particle_mesh':True,'reference_radius':1,'radius_contract':'same R120 sphere and source wing midpoint; visual radius adapted by source alpha','limitations':'原ALSshock程序闪电未伪造；源ADDN334未解析，未误接33；原受控拖曳/BSLagBone飞行拖尾/折射/动态光照未完整移植；无游戏GPU验证'}
    proof={'contract':'IRIS_DRILL_FINISHER_064','sources':[{'file':str(p),'sha256':a.a.sha(p)} for p in (blue,shock,core,wave,fire['source'])], 'chain':['IrisEXDrillSHOOT CAST8D5','SPEL8D5 -> RimSkills EXPL0B55 ALSExp','EXPL0B55 placed EXPL0B54 ALSshockExp','CAST8D4 -> script0B0B -> SPEL0B0A -> MGEF0AF4 -> EXPL0AF3 ShoutAreaExplosionSmall01','Stokes SPEL0AFB -> MGEF0AF8 -> PROJ0AF7 -> original DragonRendProjectile.nif visual','CAST Skyrim 3F9ED -> VoiceFlameWaveProject03 + AddOn64 x7'],'blue_particles':[record1,record2,record3],'unresolved_addon':{'node_name':'AddOnNode33','actual_id':334,'status':'no matching ADDN in source masters; not misbound to 33'},'stokes_uniform_scale':core_factor,'stokes_source_coverage':core_coverage,'stokes_time_scale':core_speed,'blue_wave':{'source':str(wave),'sha256':a.a.sha(wave),'source_shapes':[m['name'] for m in wm],'source_visual_instances':2,'source_projectiles':['RimSkills PROJ0AF7','RimSkills PROJ0AFD'],'uniform_scale':wave_scale,'time_scale':wave_speed,'source_visible_area_peak_age':wave_peak_age,'source_visible_coverage':wave_coverage,'radius95_by_view':(np.asarray(wave_coverage['radius95_by_view'])*wave_scale*wave_peak_cap).tolist(),'whole_instance_range_cap':wave_cap,'adaptation_note':'fixed-center R120 visual; source projectile growth uniformly constrained, all source internal proportions unchanged','placement':'fixed common wing midpoint; visual only; no projectile travel','not_ported':'BSLagBoneController flight drag and screen refraction'},'reference_exposure_adapter':core_exposure,'removed':'非源49个球形覆盖雾片；冲击环单独归一；无纹理闪光的额外遮罩','blue_uniform_scale':factor,'blue_source_coverage':coverage,'fire_uniform_scale':fire_scale,'fire_source_coverage':fire_measure,'fire_source_layer_names':[tr['mesh']for tr in fire['tracks']],'fire_radius95_by_view':(np.asarray(fire_measure['radius95_by_view'])*fire_scale).tolist(),'timing':{'blue_end':BLUE_END,'fire_begin':FIRE_BEGIN,'fire_speed':fire_speed,'source_peak_maps_to_seconds':.20,'baked':True},'render_layers':len(names),'duration':duration,'limits':asset['limitations'],'compile':'not run by policy','runtime':'not tested'}
    return asset,{'duration':duration,'samples':samples,'peak_radius':bound,'bounds':[[-bound]*3,[bound]*3],'tracks':tracks},proof

def buffers_from_blob(blob):
    from drive_effects059 import buffers_from_bytes
    return buffers_from_bytes(blob)

def replace_sub(raw,old,name,rows):
    # 保持原索引/声明/三角，只替换私有材质名和48字节顶点块；禁止使用别层三角或丢顶点alpha。
    raw=raw.replace(old.encode()+b'\n',name.encode()+b'\n',1);raw=bytearray(raw)
    struct.pack_into('<I',raw,2,len(raw));at=bytes(raw).find(struct.pack('<HI',0x5210,len(rows)*48+6));assert at>=0
    raw[at+6:at+6+len(rows)*48]=np.asarray(rows,dtype='<f4').tobytes();return bytes(raw)

def apply(a=None):
    if a is None:import author_effects as a
    from muzzle_sources063 import take_curves,append_curve
    doc=json.loads((ROOT/'docs/eight-effects.json').read_text('utf8'));previous=copy.deepcopy(a.MATS);a.MATS.update(copy.deepcopy(doc['materials']))
    asset,curve,proof=build(a);new={n:a.MATS[n] for n in asset['materials']}
    text='// 064钻天破私有源材质；其他九招及共享Shader保持。\n'
    for n,d in new.items():
        if d.get('burst_particle'):block=drill_particles.material(n,d,a.TEXTURES)
        else:
            block=shader_material(n,d)
            if 'burst_card_center' in d:block=block.replace('IrisEightVP {}','IrisBurstCardVP { param_named cardCenter float3 '+' '.join('%.9f'%v for v in d['burst_card_center'])+' }')
        # 065：NIF层名保留冒号；Ogre脚本中冒号表示继承，必须引用整个材质名。
        # 只给声明加引号，运行时CSV/网格仍使用原字符串，不改变源身份或任何视觉参数。
        declaration='material '+n+'\n';assert block.startswith(declaration)
        assert '"' not in n and '\\' not in n and '\n' not in n
        text+='material "'+n+'"\n'+block[len(declaration):]
    put(A/'iris_finisher064.material',text,'064独立源材质','限定终结层，源纹理/渐变/顶点alpha；不改共享程序或其他技能')
    for name,data in a.TEXTURES.items():put(A/name,data,'实际源纹理','源像素直接转换，不重绘素材')
    lines=(A/'effects.csv').read_text('utf8').splitlines();i=1;out=[]
    while i<len(lines):
        row=lines[i].split();end=i+1+int(row[2]);out.extend((['drill_blast iris_fx_drill_blast.mesh '+str(len(asset['materials']))+' '+' '.join('%.9f'%x for x in asset['center']+[asset['bound_radius']])]+asset['materials']) if row[0]=='drill_blast' else lines[i:end]);i=end
    put(A/'effects.csv',lines[0]+'\n'+'\n'.join(out)+'\n','064效果表','只替换drill_blast记录；数量仍22')
    lines,count=take_curves((A/'effect_curves.csv').read_text('utf8'),{'drill_blast'});append_curve(lines,'drill_blast',curve)
    put(A/'effect_curves.csv','IRIS_FX_CURVES 1 '+str(count+1)+'\n'+'\n'.join(lines)+'\n','064效果时间流','只替换钻天破；火相按源可见峰值与录像时间已烘焙，不重复加速')
    doc['assets']=[asset if x['key']=='drill_blast' else x for x in doc['assets']];doc['timelines']['drill_blast']={k:v for k,v in curve.items() if k!='tracks'};doc['materials'].update(new);doc['finisher064']=proof
    # 记录每份实际源像素出处；新增渐变也必须可追到BSA/松散文件，不只记录文件名。
    outputs={d.get(k)for d in new.values()for k in ('diffuse','palette','texture')}
    existing={(r['output'],r['source'],r['reference'])for r in doc['textures']}
    for row in a.PROVENANCE:
        key=(row['output'],row['source'],row['reference'])
        if row['output'] in outputs and key not in existing:doc['textures'].append(row);existing.add(key)
    put(ROOT/'docs/eight-effects.json',json.dumps(doc,ensure_ascii=False,indent=2),'064源效果元数据','终结实际引用链、统一尺度和明确未移植范围')
    put(ROOT/'docs/drill-source-064.json',json.dumps(proof,ensure_ascii=False,indent=2),'064源证据','真实遗漏ALSshock及源时序/范围标尺/限制')
    a.MATS.clear();a.MATS.update(previous)
if __name__=='__main__':apply()
