"""只制作Iris最小闭环资源，不编译DLL、不部署、不修改Skyrim或其他项目。"""
from pathlib import Path
import copy,hashlib,json,math,re,struct,sys
import numpy as np
from PIL import Image,ImageDraw
from io import BytesIO
from safeio import ROOT,put
# 070：握点证明表只用于开发验证，生成/读取统一移出运行assets。
from asset_paths070 import PROOFS
import port_math as m
import nif_reader as nr
from nif_geometry import read_nif
import kenshi_mod_writer as fcs
sys.path.insert(0,str(ROOT/'tools/third_party'))
from anim_skyrim import load_skyrim_animation,load_skyrim_skeleton
SOURCE=Path('E:/skyrimspecialedition/mods/soulworker_Iris');nr.SOURCE=SOURCE
GAME=Path('D:/steam/steamapps/common/Kenshi');OUT=ROOT/'package/IrisArsenal';ASSET=OUT/'assets'
HKX=SOURCE/'Meshes/actors/character/animations/DynamicAnimationReplacer/_CustomConditions/999977013/mco_powerattack1.hkx'
SKEL=SOURCE.parent/'XP32 Maximum Skeleton Special Extended/meshes/actors/character/character assets/skeleton.hkx'
SCALE=.116589590799641
C=np.array([[-1,0,0],[0,0,1],[0,1,0]],float)
R=np.array([[1,0,0],[0,0,1],[0,-1,0]],float)
PIVOT=np.array([-15.5,73.2,0.0]);LENGTH=5.633333333;N=339
ANIM='IrisArsenal_DrillProof'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def animation_filename(key,sex):
    # 身体导出与FCS引用共用文件名。旧作者引用iris_<招式>，实际导出iris_action_<招式>，
    # 引擎因找不到资源而无法出招；尤其drill旧名存在但只含DrillProof，不能仅检查文件存在。
    assert sex in ('male','female')
    return 'iris_action_'+key+'_'+sex+'.skeleton'
def chunk(t,b):return struct.pack('<HI',t,len(b)+6)+b

def slerp(a,b,u):
    a=np.asarray(a,float);b=np.asarray(b,float);d=float(a@b)
    if d<0:b=-b;d=-d
    if d>.9995:return tuple((a+(b-a)*u)/np.linalg.norm(a+(b-a)*u))
    angle=math.acos(min(1,d));return tuple((a*math.sin((1-u)*angle)+b*math.sin(u*angle))/math.sin(angle))
def pose_time(t):
    # 仅验证钻头：保留源0..3.75秒；删除后续变形终结发射，250ms回到展开起点，再逆向收回。
    # 此收回段是明确标记的原型适配，不声称源模组本来就按这条时间轴播放。
    if t<=3.75:return (t,t,0)
    if t<4:return (3.75,1.633333333,m.smooth((t-3.75)/.25))
    x=max(0,1.633333333-(t-4));return (x,x,0)
def interp(values,t,duration,quat=False):
    x=max(0,min(len(values)-1,t/duration*(len(values)-1)));i=int(x);j=min(len(values)-1,i+1);u=x-i
    return slerp(values[i],values[j],u) if quat else tuple(np.asarray(values[i])*(1-u)+np.asarray(values[j])*u)

def export_body(source, spec):
    LENGTH=source.duration;N=source.num_frames;ANIM=spec["animation"]
    HKX=Path(spec["sources"][0])
    sk=load_skyrim_skeleton(str(SKEL))
    an={name:i for i,name in enumerate(source.bone_names)};sn={name:i for i,name in enumerate(sk.bones)}
    mapping={'Bip01':'NPC COM [COM ]','Bip01 Pelvis':'NPC Pelvis [Pelv]','Bip01 Spine':'NPC Spine [Spn0]','Bip01 Spine1':'NPC Spine1 [Spn1]','Bip01 Spine2':'NPC Spine2 [Spn2]','Bip01 Neck':'NPC Neck [Neck]','Bip01 Head':'NPC Head [Head]'}
    alias={'Weapon':'WEAPON'}
    for side in ['L','R']:
        for dst,base,tag in [('Thigh','Thigh','Thg'),('Calf','Calf','Clf'),('Foot','Foot','ft '),('Toe0','Toe0','Toe'),('Clavicle','Clavicle','Clv'),('UpperArm','UpperArm','Uar'),('Forearm','Forearm','Lar'),('Hand','Hand','Hnd')]:
            name='NPC '+side+' '+base+' ['+side+tag+']';mapping['Bip01 '+side+' '+dst]=name;alias[name]='NPC '+base+' ['+tag+'].'+side
    assert all(alias.get(s,s) in an for s in list(mapping.values())+['Weapon'])
    assert sk.bones[sk.parents[sn['Weapon']]]=='NPC R Hand [RHnd]'
    qC=m.qmul(m.axis((0,1,0),180),m.axis((1,0,0),-90));Ci=m.qi(qC);qw=lambda q:m.qnorm((q[3],q[0],q[1],q[2]))
    def source_world(t=None):
        world=[]
        for j,name in enumerate(sk.bones):
            p=sk.reference_pose[j];track=an.get(alias.get(name,name));parent=sk.parents[j]
            if t is None or track is None:pos=tuple(p.translation);q=qw(p.rotation)
            else:
                ta,tb,u=t,t,0;tr=source.tracks[track]
                pos=m.lerp(interp(tr.translations,ta,source.duration),interp(tr.translations,tb,source.duration),u)
                q=qw(slerp(interp(tr.rotations,ta,source.duration,True),interp(tr.rotations,tb,source.duration,True),u))
                # Havok骨架的lock_translation是源约束，不能把锁定骨的原始动画平移直接当最终姿态。
                # 保留参考局部位移与全部旋转；COM/root等未锁骨仍用动画位置，因而不会吞掉跃起。
                if sk.lock_translation[j]:pos=tuple(p.translation)
            if parent>=0:pp,pq=world[parent];pos=m.vadd(pp,m.rotate(pq,pos));q=m.qmul(pq,q)
            world.append((pos,q))
        return world
    reference=source_world();samples=[source_world(t) for t in np.linspace(0,LENGTH,N)];audits=[]
    for sex in ['male','female']:
        bones=m.skeleton(GAME/('data/character/meshes/'+sex+'_skeleton/'+sex+'_skeleton.skeleton'));bn={x['name']:x['id'] for x in bones};rest=m.world(bones,[x['orientation'] for x in bones])
        assert set(mapping)<=set(bn) and bones[bn['Bip01 Prop2']]['parent']==bn['Bip01 R Hand']
        offset={dst:m.qmul(m.qi(reference[sn[src]][1]),m.qmul(Ci,rest[bn[dst]][1])) for dst,src in mapping.items()}
        floor=min(rest[bn['Bip01 '+side+' Foot']][0][1] for side in ['L','R']);frames=[];proof=[];maxgrip=0;left_errors=[]
        rest_bones=bones;seat_audits=[]
        for frame_index,sw in enumerate(samples):
            # 049每帧独立局部位置，禁止将上帧Pelvis校准累积进下一帧或静止骨架。
            bones=[dict(b) for b in rest_bones];pelvis_delta=(0,0,0);seat_root_dy=None
            local=[];wq=[];prop=(0,0,0)
            for bone in bones:
                name=bone['name'];parent=bone['parent']
                if name=='Bip01 Prop2':
                    desired=m.qmul(m.qmul(qC,sw[sn['Weapon']][1]),Ci)
                    delta=m.rotate(qC,m.vsub(sw[sn['Weapon']][0],sw[sn['NPC R Hand [RHnd]']][0]))
                    pos=m.rotate(m.qi(wq[parent]),m.vmul(delta,SCALE));prop=m.vsub(pos,bone['position']);q=m.qmul(m.qi(wq[parent]),desired)
                elif name in mapping:
                    desired=m.qmul(m.qmul(qC,sw[sn[mapping[name]]][1]),offset[name]);q=desired if parent<0 else m.qmul(m.qi(wq[parent]),desired)
                else:q=bone['orientation'];desired=q if parent<0 else m.qmul(wq[parent],q)
                local.append(m.qnorm(q));wq.append(m.qnorm(desired))
            wp=m.world(bones,local)
            # 只映射旋转会因两套骨架手臂长度不同而松开左手。离线两骨IK将左掌对准源相对握点；
            # 右手/WEAPON轨道不变，不在游戏内强写骨骼，不改变原生角色运动或碰撞。
            # 地震接触段先校准右手整条原生骨链，再求左手握点；不能只把锤头平移到地面而脱离双手。
            # 两套骨架臂长不同，原旋转重定向留下约5~6单位悬空。仅在落锤段以脚底高度为标尺，
            # 保持源武器朝向/右掌朝向、原骨长和跃起根轨道；离线求解后仍由FCS播放，无运行时骨写入。
            if spec['key'] in ('earthquake','vulcan'):
                t=frame_index*LENGTH/(N-1)
                # 047：引擎Y为竖直轴。远程两招在离线双手骨链抬高实际武器，枪口/特效/查询仍读取同一Prop2。
                # 标尺为最低Foot减静止站立Foot高度的脚底平面，不把离地约0.95的脚骨中心误当地面，也不乘世界坐标；发射窗口内高度为原1.5倍，发射前后0.2秒平滑接回源姿态，避开收枪高举阶段的不可达双手目标。
                # 地震原落锤校准原样保留；不伸长骨骼、不改变根运动，也不增加运行时强制位移。
                weight=(m.smooth((t-.68)/.27)*(1-m.smooth((t-2.98)/.35)) if spec['key']=='earthquake'
                        else m.smooth((t-(spec['events'][0]['time']-.25))/.2)*(1-m.smooth((t-(spec['events'][-1]['time']+.05))/.2)))
                ri=bn['Bip01 R Hand'];rq=wp[ri][1];weaponq=m.qnorm(m.qmul(m.qmul(qC,sw[sn['Weapon']][1]),Ci))
                grip_delta=np.array(m.rotate(qC,m.vsub(sw[sn['Weapon']][0],sw[sn['NPC R Hand [RHnd]']][0])))*SCALE
                head=np.array(wp[ri][0])+grip_delta+m.rotate(weaponq,[1.807138657,0,8.534358047])
                contact_floor=min(wp[bn['Bip01 '+side+' Foot']][0][1] for side in ['L','R'])
                lift=contact_floor+.6-head[1] if spec['key']=='earthquake' else .5*(head[1]-(contact_floor-floor))
                target=np.array(wp[ri][0])+[0,lift*weight,0]
                u=bn['Bip01 R UpperArm'];e=bn['Bip01 R Forearm'];clav=bn['Bip01 R Clavicle']
                cp=np.array(wp[clav][0]);lever=np.array(wp[u][0])-cp;toward=target-cp
                arm_length=np.linalg.norm(bones[e]['position'])+np.linalg.norm(bones[ri]['position'])-1e-5
                if np.linalg.norm(target-np.array(wp[u][0]))>arm_length:
                    d=np.linalg.norm(toward);l0=np.linalg.norm(lever);theta=math.acos(np.clip((toward@lever)/(d*l0),-1,1))
                    allowed=math.acos(np.clip((d*d+l0*l0-arm_length*arm_length)/(2*d*l0),-1,1))
                    if theta>allowed+1e-6:
                        turn=slerp((1,0,0,0),m.from_to(lever,toward),min(1,(theta-allowed+1e-4)/theta))
                        cq=m.qmul(turn,wp[clav][1]);local[clav]=m.qnorm(m.qmul(m.qi(wp[bones[clav]['parent']][1]),cq));wp=m.world(bones,local)
                shoulder=np.array(wp[u][0]);elbow0=np.array(wp[e][0]);hand0=np.array(wp[ri][0]);l1=np.linalg.norm(bones[e]['position']);l2=np.linalg.norm(bones[ri]['position'])
                ray=target-shoulder;distance=np.linalg.norm(ray);direction=ray/max(distance,1e-9);reach=min(l1+l2-1e-5,max(abs(l1-l2)+1e-5,distance))
                pole=elbow0-shoulder;pole-=direction*(pole@direction)
                if np.linalg.norm(pole)<1e-6:pole=np.cross(direction,[0,0,1])
                pole/=max(np.linalg.norm(pole),1e-9);along=(reach*reach+l1*l1-l2*l2)/(2*reach)
                elbow=shoulder+direction*along+pole*math.sqrt(max(0,l1*l1-along*along));hand_target=shoulder+direction*reach
                uq=m.qmul(m.from_to(elbow0-shoulder,elbow-shoulder),wp[u][1]);eq=m.qmul(m.from_to(hand0-elbow0,hand_target-elbow),wp[e][1])
                local[u]=m.qnorm(m.qmul(m.qi(wp[bones[u]['parent']][1]),uq));local[e]=m.qnorm(m.qmul(m.qi(uq),eq));local[ri]=m.qnorm(m.qmul(m.qi(eq),rq))
                # Prop2父骨已转动，局部反算仍指向源WEAPON世界朝向；不能跟着右臂再多转一次。
                local[bn['Bip01 Prop2']]=m.qnorm(m.qmul(m.qi(rq),weaponq));wp=m.world(bones,local)
            if spec['key']=='electro_cannon':
                import seated_pose
                t=frame_index*LENGTH/(N-1)
                # 只在源坐锤阶段校准；保留既有抬枪后枪口与根轨道，脚随坐姿悬起，不能再强制落地。
                seat_weight=m.smooth((t-1.15)/.35)*(1-m.smooth((t-2.75)/.35))
                seat_root_dy=floor-min(wp[bn['Bip01 '+side+' Foot']][0][1] for side in ['L','R'])
                gd=np.asarray(m.rotate(qC,m.vsub(sw[sn['Weapon']][0],sw[sn['NPC R Hand [RHnd]']][0])))*SCALE
                pelvis_delta,audit,wp=seated_pose.seat(bones,local,sw,sn,C,SCALE,seat_weight,gd);seat_audits.append(audit)
            # 059仅PA10按真实炮体轴校准枪体；普通WEAPON隐藏轨道不能当炮口，原坐锤逻辑仅留给电脉。
            driveq=None
            if spec['key']=='drive':
                import drive_shoulder059
                wp,driveq,prop=drive_shoulder059.prepare(sys.modules[__name__],bones,local,sw,sn,qC,frame_index*LENGTH/(N-1))
            rh=np.array(wp[bn['Bip01 R Hand']][0]);wq_expected=m.qnorm(m.qmul(m.qmul(qC,sw[sn['Weapon']][1]),Ci))
            if driveq is not None:wq_expected=driveq
            grip_expected=rh+np.array(m.rotate(qC,m.vsub(sw[sn['Weapon']][0],sw[sn['NPC R Hand [RHnd]']][0])))*SCALE
            left_rel=m.rotate(m.qi(sw[sn['Weapon']][1]),m.vsub(sw[sn['NPC L Hand [LHnd]']][0],sw[sn['Weapon']][0]))
            target=grip_expected+np.array(m.rotate(wq_expected,m.rotate(qC,m.vmul(left_rel,SCALE))))
            if spec['key']=='drive':target=drive_shoulder059.support_target(grip_expected,wq_expected,target,frame_index*LENGTH/(N-1))
            u=bn['Bip01 L UpperArm'];e=bn['Bip01 L Forearm'];h=bn['Bip01 L Hand']
            # 两骨链不可达时先使用真实锁骨旋转自由度，最小转角将肩部向源握点展开；
            # 不拉长骨骼、不改模型比例，也不在运行时安装IK或冻结角色。
            clav=bn['Bip01 L Clavicle'];cp=np.array(wp[clav][0]);shoulder0=np.array(wp[u][0]);toward=target-cp;lever=shoulder0-cp
            arm_length=np.linalg.norm(bones[e]['position'])+np.linalg.norm(bones[h]['position'])-1e-5
            if np.linalg.norm(target-shoulder0)>arm_length and np.linalg.norm(lever)>1e-6:
                d=np.linalg.norm(toward);l0=np.linalg.norm(lever);theta=math.acos(np.clip((toward@lever)/(d*l0),-1,1))
                allowed=math.acos(np.clip((d*d+l0*l0-arm_length*arm_length)/(2*d*l0),-1,1))
                if theta>allowed+1e-6:
                    turn=slerp((1,0,0,0),m.from_to(lever,toward),min(1,(theta-allowed+1e-4)/theta))
                    cq=m.qmul(turn,wp[clav][1]);local[clav]=m.qnorm(m.qmul(m.qi(wp[bones[clav]['parent']][1]),cq));wp=m.world(bones,local)
            shoulder=np.array(wp[u][0]);elbow0=np.array(wp[e][0]);hand0=np.array(wp[h][0]);l1=np.linalg.norm(bones[e]['position']);l2=np.linalg.norm(bones[h]['position'])
            ray=target-shoulder;distance=float(np.linalg.norm(ray));direction=ray/max(distance,1e-9)
            reach=min(l1+l2-1e-5,max(abs(l1-l2)+1e-5,distance));pole=elbow0-shoulder;pole-=direction*(pole@direction)
            if np.linalg.norm(pole)<1e-6:pole=np.cross(direction,[0,0,1])
            pole/=max(np.linalg.norm(pole),1e-9);along=(reach*reach+l1*l1-l2*l2)/(2*reach)
            elbow=shoulder+direction*along+pole*math.sqrt(max(0,l1*l1-along*along));hand_target=shoulder+direction*reach
            uq=m.qmul(m.from_to(elbow0-shoulder,elbow-shoulder),wp[u][1]);eq=m.qmul(m.from_to(hand0-elbow0,hand_target-elbow),wp[e][1])
            local[u]=m.qnorm(m.qmul(m.qi(wp[bones[u]['parent']][1]),uq));local[e]=m.qnorm(m.qmul(m.qi(uq),eq));local[h]=m.qnorm(m.qmul(m.qi(eq),wp[h][1]))
            wp=m.world(bones,local);dy=seat_root_dy if seat_root_dy is not None else floor-min(wp[bn['Bip01 '+side+' Foot']][0][1] for side in ['L','R']);maxgrip=max(maxgrip,float(np.linalg.norm(prop)))
            assert abs(dy)<60 and np.isfinite(prop).all() and maxgrip<3,(spec['key'],sex,dy,prop,maxgrip)
            # 保留源双脚离地高度；原型的逐帧落地补偿不能吞掉后空翻与跃起。
            source_floor=min(sw[sn['NPC '+side+' Foot ['+side+'ft ]']][0][2] for side in ['L','R'])
            first_floor=min(samples[0][sn['NPC '+side+' Foot ['+side+'ft ]']][0][2] for side in ['L','R'])
            dy+=(source_floor-first_floor)*SCALE
            frames.append(([m.qnorm(m.qmul(m.qi(b['orientation']),q)) for b,q in zip(bones,local)],dy,prop,pelvis_delta))
            handpos=np.array(wp[bn['Bip01 R Hand']][0])+[0,dy,0]
            grip=handpos+np.array(m.rotate(qC,m.vsub(sw[sn['Weapon']][0],sw[sn['NPC R Hand [RHnd]']][0])))*SCALE
            weaponq=m.qnorm(m.qmul(m.qmul(qC,sw[sn['Weapon']][1]),Ci))
            # 059审计必须记录实际已校准Prop2朝向，不能拿源隐藏WEAPON的旧方向当期望值。
            if driveq is not None:weaponq=driveq
            left_source=m.rotate(m.qi(sw[sn['Weapon']][1]),m.vsub(sw[sn['NPC L Hand [LHnd]']][0],sw[sn['Weapon']][0]))
            left_expected=grip+np.array(m.rotate(weaponq,m.rotate(qC,m.vmul(left_source,SCALE))))
            left_actual=np.array(wp[bn['Bip01 L Hand']][0])+[0,dy,0]
            if spec['key']=='drive':left_expected=np.asarray(target)+[0,dy,0]
            left_errors.append(float(np.linalg.norm(left_actual-left_expected)))
            proof.append([*grip,*weaponq,*left_expected])
        bones=rest_bones
        if spec['key']=='electro_cannon':
            # 050源Pelvis原点不能代表下臀表面：将真实原生蒙皮落到真实主锤顶面，固定支点防抖。
            # 只改离线Pelvis/双手动画；原武器握点、枪口、root motion和原生角色碰撞不写入。
            import surface_seat
            frames=surface_seat.calibrate(bones,frames,spec,sex)
        content=b''
        for bone in bones:
            name=bone['name'].encode()+b'\n';q=bone['orientation'];body=name+struct.pack('<H3f4f',bone['id'],*bone['position'],q[1],q[2],q[3],q[0]);content+=struct.pack('<HI',0x2000,6+len(body)-len(name))+body
        for bone in bones:
            if bone['parent']>=0:content+=chunk(0x3000,struct.pack('<HH',bone['id'],bone['parent']))
        tracks=[]
        for dst in list(mapping)+['Bip01 Prop2']:
            i=bn[dst];keys=[]
            for t,(qs,dy,p,seat_delta) in zip(np.linspace(0,LENGTH,N),frames):
                q=m.qmul(qs[i],m.axis((1,0,0),90)) if dst=='Bip01 Prop2' else qs[i]
                translation=(0,dy,float(np.interp(t,[x[0] for x in spec['motion']],[x[1] for x in spec['motion']]))) if i==0 else p if dst=='Bip01 Prop2' else seat_delta if dst=='Bip01 Pelvis' else (0,0,0)
                keys.append(chunk(0x4110,struct.pack('<f4f3f',t,q[1],q[2],q[3],q[0],*translation)))
            tracks.append(chunk(0x4100,struct.pack('<H',i)+b''.join(keys)))
        if seat_audits:
            spec.setdefault('seat049',{})[sex]={'source':'mco_powerattack6 Pelvis relative WEAPON','max_hand_error':max(x['hand_error'] for x in seat_audits),'contact_error_during_firing':max(x['pelvis_error'] for x in seat_audits if x['weight']>.999),'runtime_position_write':False}
        content+=chunk(0x4000,ANIM.encode()+b'\n'+struct.pack('<f',LENGTH)+b''.join(tracks))
        put(ASSET/animation_filename(spec['key'],sex),b'\x00\x10[Serializer_v1.80]\n'+content,'具名身体及持械动画','八招源身体/WEAPON到Prop2；保留源跃起及原生root motion，不强制坐标移动')
        put(PROOFS/('iris_'+spec['key']+'_weapon_proof_'+sex+'.csv'),'IRIS_WEAPON_PROOF 1 '+str(N)+'\n'+'\n'.join(' '.join('%.9f'%v for v in row) for row in proof)+'\n','独立源WEAPON期望值','实际序列化Prop2/模型坐标交叉验证，末三值是源左手握点')
        audits.append({'left_hand_spin_error_max':max(v for v,t in zip(left_errors,np.linspace(0,LENGTH,N)) if 1.633333333<=t<=3.75),'left_hand_error_max':max(left_errors),'left_hand_error_p95':float(np.percentile(left_errors,95)),'skeleton':sex,'frames':N,'controlled_bones':len(mapping)+1,'prop2_id':bn['Bip01 Prop2'],'max_prop_translation':maxgrip,'root_horizontal_motion':spec['motion'][-1][1]})
    spec['retarget']=audits
    # 047声明放在生产者本身，确保UpdateMod完整重建与本轮选择性导出一致。
    if spec['key']=='vulcan':
        spec['height047']={'source_reference':'sole plane = lowest Foot minus standing Foot height','vertical_axis':'engine Y','muzzle_height_scale':1.5,'blend_seconds':.2,'runtime_offset':False}
    return audits


from types import SimpleNamespace
from author_prototype import records,field,blank,refs
BASE=SOURCE/'Meshes/actors/character/animations/DynamicAnimationReplacer/_CustomConditions'
NAMES=['火焰翻滚','螺旋飞舞','地震','螺旋袭击钻天破','全力爆发','极速火神炮','脉冲之焰','极致驱动','电脉加农','破坏之锤']
KEYS=['fire_roll','spiral','earthquake','drill','full_burst','vulcan','pulse','drive','electro_cannon','hammer_combo']
def path(folder,name):return BASE/str(folder)/(name+'.hkx')
def single(folder,name,start=0,end=None,rate=1):return {'file':path(folder,name),'start':start,'end':end,'rate':rate}

def compose(parts):
    # 源片段明确切片/变速、60Hz重采样；所有事件和根移动走相同映射，不另给特效乘一遍速度。
    parsed={str(p['file']):load_skyrim_animation(str(p['file'])) for p in parts}
    first=next(iter(parsed.values()));names=first.bone_names;offset=0;mapping=[];events=[];motion=[(0.,0.)];cumulative=0
    for p in parts:
        c=parsed[str(p['file'])];assert c.bone_names==names
        lo=p['start'];hi=c.duration if p['end'] is None else p['end'];rate=p['rate'];assert 0<=lo<hi<=c.duration+1e-5
        length=(hi-lo)/rate;mapping.append((offset,offset+length,c,lo,hi,rate))
        for e in c.annotations:
            if lo<=e.time<=hi:events.append({'time':offset+(e.time-lo)/rate,'text':e.text,'source':str(p['file']),'source_time':e.time})
        curve=[(0.,0.)]+[(e.time,float(e.text.split()[2])) for e in c.annotations if e.text.startswith('animmotion ')]
        curve.sort();times=[x[0] for x in curve];vals=[x[1] for x in curve];base=float(np.interp(lo,times,vals))
        for t in np.linspace(lo,hi,max(2,round(length*60)+1)):
            motion.append((offset+(t-lo)/rate,cumulative+(float(np.interp(t,times,vals))-base)*SCALE))
        cumulative=motion[-1][1];offset+=length
    n=round(offset*60)+1;tracks=[]
    # 接缝80ms平滑只改变姿态，事件时间不变；接缝源位移清零后累加，避免组合脉冲跳回起点。
    for bone in range(len(names)):
        ps=[];qs=[]
        for t in np.linspace(0,offset,n):
            j=next((i for i,x in enumerate(mapping) if t<x[1]-1e-9),len(mapping)-1)
            a,b,c,lo,hi,rate=mapping[j];st=min(hi,lo+(t-a)*rate);tr=c.tracks[bone]
            pos=interp(tr.translations,st,c.duration);q=interp(tr.rotations,st,c.duration,True)
            if j and t-a<.08:
                prev=mapping[j-1];ptr=prev[2].tracks[bone];u=m.smooth((t-a)/.08)
                pos=m.lerp(interp(ptr.translations,prev[4],prev[2].duration),pos,u);q=slerp(interp(ptr.rotations,prev[4],prev[2].duration,True),q,u)
            ps.append(pos);qs.append(q)
        tracks.append(SimpleNamespace(translations=ps,rotations=qs))
    return SimpleNamespace(duration=offset,num_frames=n,bone_names=names,tracks=tracks),events,motion

def specs():
    p0=single(999977000,'mco_attack1',0,.65);flip=single(999977015,'combatidlea')
    # 一次首跃，三次取源短震击；不重播首跃、不同时导入Precision与HitFrame两套扣血。
    eq=[single(999977000,'mco_powerattack7',0,1.35)]+[single(999977000,'mco_powerattack8',.08,.60) for _ in range(3)]+[single(999977000,'mco_powerattack7',1.35,2.1)]
    raw=[ [p0,flip], [single(999977000,'mco_powerattack3')], eq,
          [single(999977013,'mco_powerattack1')],
          [single(999977006,'mco_powerattack1',0,2.66656,3),single(999977006,'mco_powerattack1',2.66656)],
          [single(999977000,'mco_powerattack2')],
          [single(999977006,'mco_attack1',0,1.05),single(999977000,'mco_attack8',0,.9),single(999977000,'mco_powerattack9',0,1.2)],
          # 059 NA6在源注释中转PA10；PA6是另一招坐锤电脉，不能继续复用。
          [single(999977000,'mco_powerattack10')],
          [single(999977000,'mco_powerattack6')],
          # PA1前两次纯武器挥击，接NA9后半段重砸；排除NA10踢击及全部独立特效。
          [single(999977000,'mco_powerattack1',0,.75),single(999977000,'mco_attack9',.60,2.10)] ]
    ranges=[(0,25),(0,30),(0,45),(12,70),(20,100),(0,5000),(0,5000),(0,10000),(0,45),(0,25)]
    output=[]
    for i,parts in enumerate(raw):
        clip,events,motion=compose(parts);spec={'index':i,'key':KEYS[i],'name':NAMES[i],'animation':'IrisArsenal_'+KEYS[i], 'technique':str(10+i)+'-IrisArsenal.mod','sources':[str(p['file']) for p in parts], 'source_hashes':{str(p['file']):sha(p['file']) for p in parts},'parts':[{**p,'file':str(p['file'])} for p in parts], 'duration':clip.duration,'frames':clip.num_frames,'motion':motion,'source_events':events,'attack_min':ranges[i][0],'attack_max':ranges[i][1],'weight':1,'runtime_verified':False}
        chosen=[]
        def add(e,kind,mult=1,radius=0):chosen.append({'time':e['time'],'kind':kind,'multiplier':mult,'radius':radius,'source_event':e['text']})
        for e in events:
            text=e['text']
            if i==0:
                if text=='HitFrame' and e['time']<.65:add(e,'weapon')
                if text=='PIE.$IrisBackJump':add(e,'ground_shell',2,24)
            elif i==1 and text=='HitFrame':add(e,'weapon')
            elif i==2 and text=='PIE.$IrisExplosion4':add(e,'shockwave',1.5,36)
            elif i==3:
                if text=='HitFrame' and 1.7<e['time']<3.8:add(e,'drill',.35)
                # 终结仍复用既有事件编号4；038消费者直接在两翼中心引爆，不生成飞弹。
                if text=='PIE.$IrisEXDrillSHOOT':add(e,'heavy_shell',5,120)
            # 前两刀保留连续刃线；第三刀独立球形爆炸，R90与前两刀光刃伸距一致，仍是一次3倍。
            elif i==4 and text=='HitFrame':add(e,'blade' if len(chosen)<2 else 'shockwave',2 if len(chosen)<2 else 3,4 if len(chosen)<2 else 90)
            # 火神弹碰撞与爆炸统一为用户指定球半径4.5；伤害倍率仍为0.2；074基础武器已恢复正式值，不在事件层再缩放。
            elif i==5 and text=='PIE.$IrisShoot1':add(e,'bullet',.2,4.5)
            # 031用户指定脉冲R4.5弹体、R36爆炸，三发仍各2倍；三发/各2倍保留。
            elif i==6 and text=='PIE.$IrisPlasmaShoot':add(e,'shell',2,36)
            # 059源PA10只有一次EXAnimSHOOT，连续光流仍保留用户既定4次医疗脉冲；不叠原HitFrame。
            # 从真正激发点开始每0.25秒一次，沿用原倍率默认值/INI和10000长度，只把角色圆柱改R9。
            elif i==7 and text=='PIE.$IrisEXAnimSHOOT':
                for pulse in range(4):
                    v=dict(e);v['time']=e['time']+pulse*.25;add(v,'beam',1.5,9)
            # 电脉只认四个源IrisBeam时点，不重复消费前导HitFrame；普通连击只走武器。
            elif i==8 and text=='PIE.$IrisBeam':add(e,'front_sphere',1,25)
            elif i==9 and text=='HitFrame':add(e,'weapon')
        chosen.sort(key=lambda e:e['time']);assert len(chosen)==[2,3,4,12,3,20,3,4,4,3][i],(spec['name'],chosen)
        if i==4:
            # 实际源三次非零伤害Collision_Add/Remove区间；ID1仅拖尾(DamageMult0)，不误算第四刀。
            windows=[]
            for hit in chosen:
                starts=[e for e in events if e['time']<=hit['time'] and e['text'].startswith('Collision_Add.') and '|NoTrail|' in e['text']]
                start=max(starts,key=lambda e:e['time']);identifier=re.search(r'\|ID\((\d+)\)',start['text']).group(1)
                end=min(e['time'] for e in events if e['time']>start['time'] and e['text'].startswith('Collision_Remove.') and ('|ID('+identifier+')' in e['text'] or '|ID(' not in e['text']))
                windows.append({'begin':start['time'],'end':end,'source_id':identifier})
            spec['blade_windows']=windows
        spec['events']=chosen;export_body(clip,spec);output.append(spec)
        print('MOVE_READY',spec['name'],round(clip.duration,3),len(chosen),flush=True)
    return output

def fcs_assets(moves):
    # 本体不携带种族覆盖；即使输入是历史包，也先滤掉RACE，独立补丁保持单独维护。
    base=records(OUT/'IrisArsenal.mod');out=copy.deepcopy([r for r in base if r['type']!=7 and r['key'] not in {str(i)+'-IrisArsenal.mod' for i in list(range(10,20))+list(range(30,40))}])
    # 兼容历史模板：本mod自建研究必须标记New(低4位=0)，否则FCS按修改记录查找不存在的原件。
    research=next(x for x in out if x['key']=='4-IrisArsenal.mod');research['save']&=~15
    weapon=next(x for x in out if x['key']=='1-IrisArsenal.mod');weapon['name']='伊莉丝·锤枪'
    # 074按玩家要求恢复真实Falling Sun切/钝×1.2；攻20、防10、失血2.5、室内0，穿甲50%保持。
    # 保留原字段排列和其他武器属性，完整更新也必须保持本次指定值。
    from weapon_balance053 import expected_fields,apply_existing,FCS_DESCRIPTION
    balance=expected_fields()
    for name,v in [('cut damage multiplier',balance['cut damage multiplier']),('blunt damage multiplier',balance['blunt damage multiplier']),('pierce damage multiplier',0),('min cut damage mult',0)]:field(weapon,name,'f32',v)
    apply_existing(weapon,balance)
    # WeaponCategory按本机Falling Sun/Enums验证：SKILL_HEAVY=3，ATTACK_NULL=21表示不额外覆盖动画类别。
    # 同一锤枪改为重武器；普通移动/格挡和技能攻速自然使用原生重武器通道，不运行时改共享对象。
    field(weapon,'skill category','long',3);field(weapon,'skill category animation override','long',21)
    field(weapon,'description','string','十招测试：仅本锤枪使用专属动作，权重由INI选择，FCS公共权重为0；实际命中走游戏物理与原生医疗。')
    # 048修复完整重建的字段顺序漂移：field会删旧键再追加，所以相机必须最后写，
    # 与047已验收的四字段补丁保持同一浮点字段顺序。数值不变，重复重建应得到相同字节。
    import icon_camera;icon_camera.apply(weapon,field)
    template=next(x for x in out if x['key']=='3-IrisArsenal.mod')
    field(template,'polearm','bool',False);field(template,'heavy weapons','bool',True)
    # 本次仅追加8个私有技巧及动画集；旧闭环记录保留给DrillProofOnly诊断模式，其他长柄刀不进入。
    for s in moves:
        anim=blank(112,30+s['index'],'Iris '+s['key']+' animations');field(anim,'preprocess','bool',True)
        for sex in ['male','female']:field(anim,sex+' animation','filename','./mods/IrisArsenal/assets/'+animation_filename(s['key'],sex))
        tech=copy.deepcopy(template);tech['key']=s['technique'];tech['name']=s['name'];tech['id']=0
        field(tech,'anim name','string',s['animation']);field(tech,'gains ground','bool',abs(s['motion'][-1][1])>.01 or s['key']=='fire_roll')
        field(tech,'attack distance','f32',s['attack_max']);field(tech,'attack distance min vs static','f32',s['attack_min'])
        field(tech,'anim speed mult','f32',1);field(tech,'chance','f32',0);field(tech,'disabled','bool',True)
        # 为避免原生Impact与插件物理重复扣血，公共技巧保留一个零伤害节拍；私有maxTargetHits运行时再次归零。
        field(tech,'anim blocked frame 1','f32',99);field(tech,'power 1','long',0);out.extend([anim,tech])
    assert not any(r['type']==7 for r in out),'本体不得生成种族动画覆盖'
    header=struct.pack('<I',2)+b''.join(fcs.w_str(s) for s in ['Codex',FCS_DESCRIPTION,'',''])+b'\0'*10
    data=struct.pack('<II',17,len(header))+header+struct.pack('<II',100,len(out))+b''.join(fcs.write_record(r) for r in out)
    put(OUT/'IrisArsenal.mod',data,'八招隔离FCS记录','074武器正式基础伤害与加成；公共chance0/disabled、native gainsGround和FCS起手距离保持')
    assert fcs.roundtrip(str(OUT/'IrisArsenal.mod'))['identical']

def main():
    moves=specs();fcs_assets(moves)
    put(ROOT/'docs/eight-moves.json',json.dumps({'version':'0.4.2','contract':'IRIS_EIGHT_042','routing':{'ranged_checkbox_only':['vulcan','pulse','drive','electro_cannon','hammer_combo'],'melee':['fire_roll','spiral','earthquake','drill','full_burst','electro_cannon','hammer_combo'],'interval_native_reload_units':1,'interval_ini_key':'RangedActionInterval','inventory_weapon_unchanged':True},'moves':moves,'balances':'测试起点，不宣称原游戏倍率；FCS距离与INI权重可调','compiled':False,'deployed':False},ensure_ascii=False,indent=2),'八招源身份/时序/重定向合同','源HKX时间统一映射；火神20发、脉冲3发、地震4震、钻头11脉冲加炮弹')
    blade=next(x for x in moves if x['key']=='full_burst')['blade_windows']
    put(ASSET/'blade_windows.csv','IRIS_BLADE_WINDOWS 1 3\n'+'\n'.join('%d %.9f %.9f'%(i,w['begin'],w['end']) for i,w in enumerate(blade))+'\n','三段源刀刃窗口','严格取变速后Collision_Add/Remove有效区间，HitFrame仍仅三个伤害身份')
    # 视觉提示取真实源HKX事件，和健康事件分开序列化；不用散落在C++的猜测时间。
    aliases={'PIE.$IrisBackfire':'backfire','PIE.$IrisAnim':'gun','PIE.$IrisOffAll':'off','PIE.$IrisExplosion':'ignition','PIE.$IrisCharge3':'charge_halo','PIE.$IrisEXDrill2':'wing','PIE.$IrisEXDrillOFF':'wing_off'}
    cues=[]
    for spec in moves:
        for e in spec['source_events']:
            # 原PayloadInterpreter对EXDrill2延迟0.02秒；OFF不延迟，独立于健康事件。
            if spec['index']!=9 and e['text'] in aliases:cues.append((spec['index'],aliases[e['text']],e['time']+(.02 if aliases[e['text']]=='wing' else 0)))
    cues=sorted(set(cues));assert len(cues)<=64
    put(ASSET/'effect_cues.csv','IRIS_FX_CUES 1 '+str(len(cues))+'\n'+'\n'.join('%d %s %.9f'%v for v in cues)+'\n','源视觉触发时间流','源尾焰/枪体/清理/点火/charge3提示独立时钟，不新增伤害')
    lines=['IRIS_EIGHT 1 10']
    kinds={'weapon':0,'ground_shell':1,'shockwave':2,'drill':3,'heavy_shell':4,'blade':5,'bullet':6,'shell':7,'beam':8,'front_sphere':9}
    for s in moves:
        lines.append('%d %s %s %.9f %d %.9f %.9f'%(s['index'],s['key'],s['animation'],s['duration'],len(s['events']),s['attack_min'],s['attack_max']))
        lines.extend('%.9f %d %.9f %.9f'%(e['time'],kinds[e['kind']],e['multiplier'],e['radius']) for e in s['events'])
    put(ASSET/'moves.csv','\n'.join(lines)+'\n','八招运行时事件流','编号/帧长/事件类型/倍率/半径；与身体FCS时间共同消费，严格8招和事件数')
    # 102只在旧源动作导出全部结束后统一重排drive的数据时钟；防止以后完整重建恢复旧蓄力/射程。
    # 特效仍使用原源时间曲线，由运行时反解；FCS总速率保持1，避免开火后也翻倍。
    import projectile_drive102;projectile_drive102.prepare()
if __name__=='__main__':main()
