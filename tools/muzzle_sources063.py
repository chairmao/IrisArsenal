"""063只恢复火神两份源准星与脉冲原发射爆发；不编译、不部署、不碰战斗判定。"""
# 070：移除已由AST与跨模块引用核实的未使用导入；原资源生产算法保持。
from pathlib import Path
import copy,json,struct
import numpy as np
from safeio import ROOT,put
from fx_timeline import timeline
from effect_data059 import buffers,curves
from drive_effects059 import raw_sub,mesh_blob,shader_material
from nif_geometry import read_nif
A=ROOT/'package/IrisArsenal/assets'

def take_curves(text,replaced):
    lines=text.splitlines();out=[];i=1;count=0
    while i<len(lines):
        row=lines[i].split();end=i+1+int(row[1])*int(row[2])
        if row[0] not in replaced:out.extend(lines[i:end]);count+=1
        i=end
    return out,count

def append_curve(lines,key,d):
    lines.append('%s %d %d %.9f %.9f'%(key,len(d['tracks']),d['samples'],d['duration'],d['peak_radius']))
    for tr in d['tracks']:lines.extend(' '.join('%.9f'%float(v) for v in state) for state in tr['frames'])

def asset(e,key,path,meshes,d):
    blocks={b['index']:b for b in e.nr.parse(path)['parsed_blocks']}
    blob,names,p=e.mesh_bytes(meshes,blocks)
    lo=np.minimum(p.min(0),d['bounds'][0]);hi=np.maximum(p.max(0),d['bounds'][1]);peak=max(float(np.linalg.norm(p,axis=1).max()),d['peak_radius'])
    blob=blob[:-34]+e.a.chunk(0x9000,struct.pack('<7f',*lo,*hi,peak))
    put(A/('iris_fx_'+key+'.mesh'),blob,'063原准星几何','源顶点/UV/材质/默认矩阵保持；包围包含原控制器整段运动')
    row={'key':key,'source':str(path),'sha256':e.a.sha(path),'materials':names,'min':p.min(0).tolist(),'max':p.max(0).tolist(),'center':((p.min(0)+p.max(0))*.5).tolist(),'bound_radius':float(np.linalg.norm(p-(p.min(0)+p.max(0))*.5,axis=1).max()),'limitations':'真实源几何与NiTimeController；不是相机HUD或手绘替代环'}
    return row

def apply(e=None):
    if e is None:
        import author_effects as e
    original=copy.deepcopy(e.MATS);doc=json.loads((ROOT/'docs/eight-effects.json').read_text('utf8'));e.MATS.update(copy.deepcopy(doc['materials']))
    source=e.S/'Meshes/SW/Iris';replacements=[];timelines={};record={}
    # IrisAnim同时施放84B(ARMO85B/anim.nif)与85C(ARTO84C/anim1.nif)。
    # 小组以Prn=Weapon附着；大组原ARTO包含3BA参考身体，必须排除身体后仍按角色根挂接。
    path=source/'anim.nif';small,_=read_nif(path);small=[m for m in small if not any('vivianwitch' in t.lower() for t in m['textures'])]
    d=timeline(path,small,None,e.a.C,e.a.SCALE,loop_transforms=True)
    replacements.append(asset(e,'gun',path,small,d));timelines['gun']=d
    path=source/'anim1.nif';large,_=read_nif(path,excluded_shapes=('3BA',));assert len(large)==8
    b=timeline(path,large,None,e.a.C,e.a.SCALE,loop_transforms=True)
    body=asset(e,'vulcan_body',path,large,b);replacements.append(body);timelines['vulcan_body']=b
    record['vulcan']={'small_source':str(source/'anim.nif'),'small_sha256':e.a.sha(source/'anim.nif'),'large_source':str(path),'large_sha256':e.a.sha(path),'small_shapes':len(small),'large_shapes':len(large),'excluded':['3BA body','missing vivian rod helper'],'small_controller':{'frequency':5,'start':0,'stop':4.125,'cycle':'loop','rotation_y':[[0,0],[2.0416998863220215,3.1415998935699463],[4.125,6.283199787139893]]},'large_controller':{'frequency':4,'start':0,'stop':8,'cycle':'reverse'},'clock':'IrisAnim cue-relative game animation seconds','small_spell_seconds':2.4,'large_spell_seconds':2.2,'chain':['IrisAnim','SPEL84B/MGEF859/ARMO85B -> anim.nif','SPEL85C/MGEF855/ARTO84C -> anim1.nif']}
    # IrisPlasmaShoot第二条CAST824 -> MGEF812 -> EXPL810，明确引用ShoutAreaExplosionWarm0。
    # 复用已核验的原三曲面/275火花/原LUT/时钟；不拿飞行圆盘、通用红蓝准星或别招FireWave冒充枪口。
    base=next(x for x in doc['assets'] if x['key']=='electro_area');path=Path(base['source']);assert e.a.sha(path)==base['sha256']
    states,duration,peak=curves(A/'effect_curves.csv','electro_area');parts=buffers(A/'iris_fx_electro_area.mesh');moves=json.loads((ROOT/'docs/eight-moves.json').read_text('utf8'))['moves'];offsets=[x['time']-moves[6]['events'][0]['time'] for x in moves[6]['events']];assert len(offsets)==3
    end=duration+max(offsets);samples=round(end*30)+1;assert 0<end<=8 and samples<=241
    subs=[];tracks=[];names=[];bounds=[]
    for offset in offsets:
        for index,(name,raw) in enumerate(parts):
            rows=raw.copy();assert rows.shape[1]==12
            if doc['materials'][name].get('burst_particle'):
                # GPU粒子按整套局部秒积分，出生时间平移；不改原位置、速度、半径、寿命或颜色。
                rows[:,6]+=offset
            points=rows[:,:3];bounds.extend(points);subs.append(raw_sub(e.a,name,rows,__import__('scene_geometry').mesh(A/'iris_fx_electro_area.mesh')[index]['tri']));names.append(name)
            source_states=states[index];frames=[]
            for t in np.linspace(0,end,samples):
                age=t-offset;k=np.clip(age/duration*(len(source_states)-1),0,len(source_states)-1);i=int(k);j=min(len(source_states)-1,i+1);state=(source_states[i]*(1-(k-i))+source_states[j]*(k-i)).tolist()
                if age<0 or age>=duration:state[3]=0
                frames.append(state)
            tracks.append({'mesh':str(offset)+':'+name,'frames':frames})
    # 源三维包围已包含相机朝向卡片及粒子寿命；三次触发仅平移时间，空间包围不变。
    points=np.asarray(bounds).copy();center=(points.max(0)+points.min(0))*.5
    bound=max(peak,float(np.linalg.norm(points,axis=1).max()));bounds.extend([[-bound]*3,[bound]*3]);blob=mesh_blob(e.a,subs,bounds)
    put(A/'iris_fx_pulse_muzzle.mesh',blob,'脉冲原发射火焰','原824爆发三次触发，12源层；独立源时间，不绘制准星，不接触健康或碰撞')
    pulse={'key':'pulse_muzzle','source':str(path),'sha256':base['sha256'],'materials':names,'center':center.tolist(),'bound_radius':float(np.linalg.norm(points-center,axis=1).max()),'min':points.min(0).tolist(),'max':points.max(0).tolist(),'particle_mesh':True,'limitations':'原824曲面/275火花，每发独立原曲线；沿枪口挂接及显示半径6为Kenshi视觉标尺适配，非原伤害半径'}
    replacements.append(pulse);timelines['pulse_muzzle']={'duration':end,'samples':samples,'peak_radius':bound,'tracks':tracks}
    record['pulse']={'chain':['PIE.$IrisPlasmaShoot second CAST','SPEL 04000824','MGEF 04000812','EXPL 04000810','SW/Iris/ShoutAreaExplosionWarm0.nif'],'source_sha256':base['sha256'],'trigger_offsets':offsets,'source_layers_per_shot':4,'visible_radius_adapter':6,'unchanged':'all source geometry/texture/colour/UV/relative proportions; damage R36 unchanged','no_reticle':True,'birth_times_shifted_only':True,'reference_match':'用户同意以原枪口橙色扩散层作为本轮方向；不声称另有独立火苗已唯一定位','full_flame_verified':False,'source_file_scale_note':'复用同源单位半径，整套相似缩放为枪口层；不是把AOE伤害范围改为6'}
    # 准星新材质仅追加独立文件；旧iris_eight.material、所有其他招式材质块保持字节不变。
    text='// 063火神大准星：原anim1的八片源几何及同像素PNG；不包含3BA身体。\n'+'\n'.join(shader_material(name,e.MATS[name]) for name in dict.fromkeys(body['materials']))
    put(A/'iris_muzzle063.material',text,'063独立源材质','复用已验证IrisEight程序与源像素；不改共享Shader源码或其他招式材质')
    for name,data in e.TEXTURES.items():put(A/name,data,'实际源贴图','源像素转换/复用同一缓存名字，不自制或改色')
    lines=(A/'effects.csv').read_text('utf8').splitlines();rows=[];i=1;keys={x['key'] for x in replacements};n=0
    while i<len(lines):
        row=lines[i].split();last=i+1+int(row[2])
        if row[0] not in keys:rows.extend(lines[i:last]);n+=1
        i=last
    for item in replacements:
        rows.append(item['key']+' iris_fx_'+item['key']+'.mesh '+str(len(item['materials']))+' '+' '.join('%.9f'%v for v in item['center']+[item['bound_radius']]));rows.extend(item['materials'])
    put(A/'effects.csv','IRIS_FX 4 '+str(n+len(replacements))+'\n'+'\n'.join(rows)+'\n','063运行效果表','只替换gun并追加vulcan_body/pulse_muzzle；其他效果记录原样保留')
    lines,count=take_curves((A/'effect_curves.csv').read_text('utf8'),keys)
    for key,d in timelines.items():append_curve(lines,key,d)
    put(A/'effect_curves.csv','IRIS_FX_CURVES 1 '+str(count+len(timelines))+'\n'+'\n'.join(lines)+'\n','063分层源时钟','火神源循环与脉冲三次原爆发；其他效果原行保持')
    for item in replacements:
        key=item['key'];doc['assets']=[x for x in doc['assets'] if x['key']!=key]+[item];doc['timelines'][key]={k:v for k,v in timelines[key].items() if k!='tracks'}
    doc['materials'].update({n:e.MATS[n] for n in body['materials']});doc['muzzle063']=record
    put(ROOT/'docs/eight-effects.json',json.dumps(doc,ensure_ascii=False,indent=2),'063来源元数据','新增两招原来源/控制器/触发时序/明确视觉适配边界，其他招式记录保持')
    put(ROOT/'docs/muzzle-source-063.json',json.dumps(record,ensure_ascii=False,indent=2),'063源引用证据','视频92..96/65..69与ESP/INI/NIF可核对链；不假称完整NiPSys或游戏实测')
    e.MATS.clear();e.MATS.update(original)
if __name__=='__main__':apply()
