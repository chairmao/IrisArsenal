"""049：实际序列化坐姿/枪口、源火花、库存图与更新边界；不执行游戏或编译器。"""
import json,hashlib,sys,struct,tempfile
from pathlib import Path
from io import BytesIO
import numpy as np
from PIL import Image
from safeio import ROOT
import author_moves as a,port_math as m,verify_prototype as v
from test_drill_visibility import buffers,curves

def source_frames(clip,frame_count):
    # 独立从源HKX与锁定平移骨架取世界位姿，不读取作者输出的seat049期望字段。
    sk=a.load_skyrim_skeleton(str(a.SKEL));aliases={'Weapon':'WEAPON'}
    for side in 'LR':
        for base,tag in [('Thigh','Thg'),('Calf','Clf'),('Foot','ft '),('Toe0','Toe'),('Clavicle','Clv'),('UpperArm','Uar'),('Forearm','Lar'),('Hand','Hnd')]:aliases[f'NPC {side} {base} [{side}{tag}]']=f'NPC {base} [{tag}].{side}'
    ids={n:i for i,n in enumerate(sk.bones)};tracks={n:i for i,n in enumerate(clip.bone_names)};result=[]
    for t in np.linspace(0,clip.duration,frame_count):
        world=[]
        for i,name in enumerate(sk.bones):
            ref=sk.reference_pose[i];p=tuple(ref.translation);q=(ref.rotation[3],*ref.rotation[:3]);index=tracks.get(aliases.get(name,name))
            if index is not None:
                tr=clip.tracks[index];xyzw=a.interp(tr.rotations,t,clip.duration,True);q=(xyzw[3],*xyzw[:3])
                if not sk.lock_translation[i]:p=a.interp(tr.translations,t,clip.duration)
            par=sk.parents[i]
            if par>=0:pp,pq=world[par];p=m.vadd(pp,m.rotate(pq,p));q=m.qmul(pq,q)
            world.append((p,q))
        result.append(world)
    return ids,result

def actual_frames(path,spec):
    bones,L,tracks=v.skeleton(path,spec['animation']);ids={b['name']:b['id'] for b in bones};result=[]
    for k in range(spec['frames']):
        world=[]
        for bone in bones:
            row=tracks[bone['id']][k] if bone['id'] in tracks else (0,0,0,0,1,0,0,0);q=m.qmul(bone['orientation'],(row[4],*row[1:4]));p=m.vadd(bone['position'],row[5:]);parent=bone['parent']
            if parent>=0:pp,pq=world[parent];p=m.vadd(pp,m.rotate(pq,p));q=m.qmul(pq,q)
            world.append((p,q))
        result.append(world)
    return ids,result,bones

def verify_049():
    package=ROOT/'package/IrisArsenal';A=package/'assets';moves=json.loads((ROOT/'docs/eight-moves.json').read_text('utf8'))['moves'];results=[]
    clip=a.load_skyrim_animation(str(a.single(999977000,'mco_powerattack6')['file']));sn,source=source_frames(clip,moves[8]['frames'])
    # 059用户纠正drive应站立肩持；仅electro保留源PA6坐姿，drive由test_drive059验收。
    for i in (8,):
        spec=moves[i];times=np.linspace(0,spec['duration'],spec['frames']);active=np.flatnonzero((times>=1.5)&(times<=2.75))
        for sex in ('male','female'):
            ids,world,bones=actual_frames(A/f"iris_action_{spec['key']}_{sex}.skeleton",spec);errors=[]
            for k in active:
                # 根轨道自动相消；检查真正序列化的臀部与模型握点相对位置，不只检查自报审计。
                expected=a.C@(np.asarray(source[k][sn['NPC Pelvis [Pelv]']][0])-source[k][sn['Weapon']][0])*a.SCALE
                actual=np.asarray(world[k][ids['Bip01 Pelvis']][0])-world[k][ids['Bip01 Prop2']][0]
                errors.append(float(np.linalg.norm(actual-expected)))
            if 'seat050' in spec:
                # 050明确修正了049错误的原点验收：真实蒙皮必须位于实际实体顶面，不能再要求腰靠原点。
                from test_surface050 import surface_contact
                contact=surface_contact(spec,sex,ids,world,bones)
                errors=contact['contact_error_frames']
            else:assert max(errors)<1e-4,(spec['key'],sex,max(errors))
            native=m.skeleton(a.GAME/f'data/character/meshes/{sex}_skeleton/{sex}_skeleton.skeleton')
            assert all(np.allclose(b['position'],n['position']) for b,n in zip(bones,native)), '不得修改静止骨长'
            results.append({'move':spec['key'],'sex':sex,('seat_surface_gap_error' if 'seat050' in spec else 'seat_relative_error'):max(errors),'rest_bone_lengths_unchanged':True})
    fx=json.loads((ROOT/'docs/eight-effects.json').read_text('utf8'));e=json.loads((ROOT/'docs/electro-source-049.json').read_text('utf8'));asset=next(x for x in fx['assets'] if x['key']=='electro_area')
    assert hashlib.sha256(Path(e['source']).read_bytes()).hexdigest()==e['sha256'] and e['source_billboards']==['Glow:0']
    assert len(asset['materials'])==4 and abs(fx['timelines']['electro_burst']['source_xy_scale049']-25/e['visible_source_radius'])<1e-9
    layer=e['serialized_particle_layers'][0];assert layer['source_capacity']==302 and len(layer['particles'])==275
    buf=buffers(A/'iris_fx_electro_area.mesh');name,p=buf[-1];assert name==layer['material'] and np.allclose(p[::4,:10],layer['particles'],atol=2e-6)
    state,duration,peak=curves(A/'effect_curves.csv','electro_area');assert state.shape==(4,151,25) and duration==5
    mat=fx['materials'][asset['materials'][0]];assert 'burst_card_center' in mat and mat['emission']==[.46274515986442566,.5686274766921997,.6431372761726379]
    # 验真实粒子全寿命包围，包含出生点、速度和尺寸；仅存活期间参与画面，不添加伤害事件。
    raw=(A/'iris_fx_electro_area.mesh').read_bytes();bounds=struct.unpack('<7f',raw[-28:]);largest=0
    for pt in layer['particles']:
        for age in np.linspace(0,pt[7],13):
            q=np.asarray(pt[:3])+np.asarray(pt[3:6])*age;r=pt[8]*np.interp(age/pt[7],np.linspace(0,1,5),layer['size_curve'])*2**.5
            largest=max(largest,float(np.linalg.norm(np.abs(q)+r)))
    assert largest<=bounds[6]+1e-5
    from inventory_icon049 import NAMES,install
    image=Image.open(package/'icons'/NAMES[0]);bbox=image.getchannel('A').point(lambda x:255 if x>=16 else 0).getbbox()
    assert image.size==(512,128) and bbox[2]-bbox[0]>480 and bbox[3]-bbox[1]>108 and 0<bbox[0]<bbox[2]<512
    with tempfile.TemporaryDirectory(prefix='Iris049-',dir='D:/CodexWorkSpace') as tmp:
        game=Path(tmp)/'game';target=game/'data/icons'/NAMES[0];target.parent.mkdir(parents=True);target.write_bytes(b'old');other=target.with_name('1-Other.mod.png');other.write_bytes(b'other')
        rows=install(game,[Path(tmp)/'a',Path(tmp)/'b'],lambda:None);assert target.read_bytes()==(package/'icons'/NAMES[0]).read_bytes() and other.read_bytes()==b'other' and len(rows)==1
        assert all(Path(p).read_bytes()==b'old' for p in rows[0]['backups']);assert install(game,[Path(tmp)/'a',Path(tmp)/'b'],lambda:None)==[]
        target.write_bytes(b'keep');blocked=Path(tmp)/'blocked';blocked.write_bytes(b'file')
        try:install(game,[Path(tmp)/'ok',blocked],lambda:None);raise AssertionError('备份失败仍写缓存')
        except OSError:pass
        assert target.read_bytes()==b'keep'
        def running():raise RuntimeError('game running')
        try:install(game,[Path(tmp)/'a',Path(tmp)/'b'],running);raise AssertionError('运行中仍写缓存')
        except RuntimeError:pass
        assert target.read_bytes()==b'keep'
    return {'seat':results,'source_particles':275,'source_particle_capacity':302,'source_colour_preserved':True,'source_world_scale':e['world_scale'],'particle_bound':largest,'icon_bounds':bbox,'inventory_footprint':[10,2],'cache_isolation':True,'CPP_changed':False,'compiled':False,'GPU_tested':False}
if __name__=='__main__':print(json.dumps(verify_049(),ensure_ascii=False,indent=2))
