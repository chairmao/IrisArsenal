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

def body_assets():
    source=load_skyrim_animation(str(HKX));sk=load_skyrim_skeleton(str(SKEL))
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
                ta,tb,u=pose_time(t);tr=source.tracks[track]
                pos=m.lerp(interp(tr.translations,ta,source.duration),interp(tr.translations,tb,source.duration),u)
                q=qw(slerp(interp(tr.rotations,ta,source.duration,True),interp(tr.rotations,tb,source.duration,True),u))
            if parent>=0:pp,pq=world[parent];pos=m.vadd(pp,m.rotate(pq,pos));q=m.qmul(pq,q)
            world.append((pos,q))
        return world
    reference=source_world();samples=[source_world(t) for t in np.linspace(0,LENGTH,N)];audits=[]
    for sex in ['male','female']:
        bones=m.skeleton(GAME/('data/character/meshes/'+sex+'_skeleton/'+sex+'_skeleton.skeleton'));bn={x['name']:x['id'] for x in bones};rest=m.world(bones,[x['orientation'] for x in bones])
        assert set(mapping)<=set(bn) and bones[bn['Bip01 Prop2']]['parent']==bn['Bip01 R Hand']
        offset={dst:m.qmul(m.qi(reference[sn[src]][1]),m.qmul(Ci,rest[bn[dst]][1])) for dst,src in mapping.items()}
        floor=min(rest[bn['Bip01 '+side+' Foot']][0][1] for side in ['L','R']);frames=[];proof=[];maxgrip=0;left_errors=[]
        for sw in samples:
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
            rh=np.array(wp[bn['Bip01 R Hand']][0]);wq_expected=m.qnorm(m.qmul(m.qmul(qC,sw[sn['Weapon']][1]),Ci))
            grip_expected=rh+np.array(m.rotate(qC,m.vsub(sw[sn['Weapon']][0],sw[sn['NPC R Hand [RHnd]']][0])))*SCALE
            left_rel=m.rotate(m.qi(sw[sn['Weapon']][1]),m.vsub(sw[sn['NPC L Hand [LHnd]']][0],sw[sn['Weapon']][0]))
            target=grip_expected+np.array(m.rotate(wq_expected,m.rotate(qC,m.vmul(left_rel,SCALE))))
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
            wp=m.world(bones,local);dy=floor-min(wp[bn['Bip01 '+side+' Foot']][0][1] for side in ['L','R']);maxgrip=max(maxgrip,float(np.linalg.norm(prop)))
            assert abs(dy)<30 and np.isfinite(prop).all() and maxgrip<30
            frames.append(([m.qnorm(m.qmul(m.qi(b['orientation']),q)) for b,q in zip(bones,local)],dy,prop))
            handpos=np.array(wp[bn['Bip01 R Hand']][0])+[0,dy,0]
            grip=handpos+np.array(m.rotate(qC,m.vsub(sw[sn['Weapon']][0],sw[sn['NPC R Hand [RHnd]']][0])))*SCALE
            weaponq=m.qnorm(m.qmul(m.qmul(qC,sw[sn['Weapon']][1]),Ci))
            left_source=m.rotate(m.qi(sw[sn['Weapon']][1]),m.vsub(sw[sn['NPC L Hand [LHnd]']][0],sw[sn['Weapon']][0]))
            left_expected=grip+np.array(m.rotate(weaponq,m.rotate(qC,m.vmul(left_source,SCALE))))
            left_actual=np.array(wp[bn['Bip01 L Hand']][0])+[0,dy,0]
            left_errors.append(float(np.linalg.norm(left_actual-left_expected)))
            proof.append([*grip,*weaponq,*left_expected])
        content=b''
        for bone in bones:
            name=bone['name'].encode()+b'\n';q=bone['orientation'];body=name+struct.pack('<H3f4f',bone['id'],*bone['position'],q[1],q[2],q[3],q[0]);content+=struct.pack('<HI',0x2000,6+len(body)-len(name))+body
        for bone in bones:
            if bone['parent']>=0:content+=chunk(0x3000,struct.pack('<HH',bone['id'],bone['parent']))
        tracks=[]
        for dst in list(mapping)+['Bip01 Prop2']:
            i=bn[dst];keys=[]
            for t,(qs,dy,p) in zip(np.linspace(0,LENGTH,N),frames):
                q=m.qmul(qs[i],m.axis((1,0,0),90)) if dst=='Bip01 Prop2' else qs[i]
                translation=(0,dy,0) if i==0 else p if dst=='Bip01 Prop2' else (0,0,0)
                keys.append(chunk(0x4110,struct.pack('<f4f3f',t,q[1],q[2],q[3],q[0],*translation)))
            tracks.append(chunk(0x4100,struct.pack('<H',i)+b''.join(keys)))
        content+=chunk(0x4000,ANIM.encode()+b'\n'+struct.pack('<f',LENGTH)+b''.join(tracks))
        put(ASSET/('iris_drill_'+sex+'.skeleton'),b'\x00\x10[Serializer_v1.80]\n'+content,'具名身体及持械动画','源钻头前段＋闭环收回；源WEAPON到Prop2，匹配原生Y轴装备')
        put(PROOFS/('iris_weapon_proof_'+sex+'.csv'),'IRIS_WEAPON_PROOF 1 '+str(N)+'\n'+'\n'.join(' '.join('%.9f'%v for v in row) for row in proof)+'\n','独立源WEAPON期望值','实际序列化Prop2/模型坐标交叉验证，末三值是源左手握点')
        audits.append({'left_hand_spin_error_max':max(v for v,t in zip(left_errors,np.linspace(0,LENGTH,N)) if 1.633333333<=t<=3.75),'left_hand_error_max':max(left_errors),'left_hand_error_p95':float(np.percentile(left_errors,95)),'skeleton':sex,'frames':N,'controlled_bones':len(mapping)+1,'prop2_id':bn['Bip01 Prop2'],'max_prop_translation':maxgrip,'root_horizontal_motion':0})
    put(ROOT/'docs/body-retarget.json',json.dumps({'source':str(HKX),'sha256':sha(HKX),'source_length':source.duration,'output_length':LENGTH,'reference':str(SKEL),'reference_sha256':sha(SKEL),'adaptation':'source0..3.75;blend250ms to1.633;reverse1.633..0. Not full source ultimate.','skeletons':audits,'unresolved':'头/双手贴合与替换骨架须实机，不假定所有人形布局相同'},ensure_ascii=False,indent=2),'重定向证据','记录源身份、源/输出时钟与闭环适配边界')

def mesh_bytes(meshes,normal=False,drill=False):
    subs=[];bounds=[]
    for x in meshes:
        p=np.array(x['vertices'])@x['matrix'][:3,:3].T+x['matrix'][:3,3]
        if drill:p-=PIVOT
        p=p@C.T*SCALE;n=np.array(x['normals'])@np.linalg.inv(x['matrix'][:3,:3])@C.T;n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-10)
        if normal:p=p@R.T;n=n@R.T
        bounds.extend(p);mat=material(x)
        decl=chunk(0x5100,b''.join(chunk(0x5110,struct.pack('<5H',0,t,s,o,0)) for t,s,o in [(2,1,0),(2,4,12),(1,7,24)]))
        vb=b''.join(struct.pack('<8f',*pos,*norm,*uv) for pos,norm,uv in zip(p,n,x['uv']))
        geom=chunk(0x5000,struct.pack('<I',len(p))+decl+chunk(0x5200,struct.pack('<HH',0,32)+chunk(0x5210,vb)))
        idx=[i for tri in x['triangles'] for i in tri];assert len(p)<65536
        subs.append(chunk(0x4000,mat.encode()+b'\n'+struct.pack('<?I?',False,len(idx),False)+struct.pack('<%dH'%len(idx),*idx)+geom))
    p=np.array(bounds);data=b'\x00\x10[MeshSerializer_v1.41]\n'+chunk(0x3000,b'\0'+b''.join(subs)+chunk(0x9000,struct.pack('<7f',*p.min(0),*p.max(0),np.linalg.norm(p,axis=1).max())))
    return data,p
MATERIALS={};TEXTURES={}
def texture(ref):
    if not ref:return 'iris_white.dds'
    raw=ref.replace('\\','/');match=re.search(r'(?i)(?:^|/)textures/',raw);assert match,ref
    tail=raw[match.start():].lstrip('/');p=SOURCE/tail;assert p.is_file(),'缺源纹理: '+str(p)
    name='iris_'+sha(p)[:16]+'.dds';TEXTURES[name]=p;return name

def material(mesh):
    sh=mesh['shader_data'];diff=texture(mesh['textures'][0]);glow=texture(mesh['textures'][2]) if len(mesh['textures'])>2 else 'iris_white.dds'
    emission=sh.get('emissive',[0,0,0]);mult=sh.get('emissive_mult',0)/16
    contract={'diffuse':diff,'glow':glow,'emission':[v*mult for v in emission],'alpha':sh.get('alpha',1),'uv_offset':sh.get('uv_offset',[0,0]),'uv_scale':sh.get('uv_scale',[1,1]),'optical':len(mesh['vertices'])==4}
    name='IrisArsenal/'+hashlib.sha256(json.dumps(contract,sort_keys=True).encode()).hexdigest()[:12];MATERIALS[name]=contract;return name

def visual_assets():
    normal,_=read_nif(SOURCE/'Meshes/SW/Iris/2.nif');drill,_=read_nif(SOURCE/'Meshes/SW/Iris/EXDrill1.nif');assert len(normal)==2 and len(drill)==19
    data,npnt=mesh_bytes(normal,normal=True);put(ASSET/'iris_weapon.mesh',data,'原生Y轴普通武器','保留源2.nif正常枪体、坐标原点及原生挂点；不写角色实体变换')
    data,dp=mesh_bytes(drill,drill=True);put(ASSET/'iris_drill.mesh',data,'真实三维附加钻头','源15个实体部件及4个光学层，围绕真实TwinChakrams轴旋转；不隐藏正常装备')
    solid=[]
    for x in drill[:15]:solid.extend(np.array(x['vertices'])@x['matrix'][:3,:3].T+x['matrix'][:3,3]-PIVOT)
    solid=np.array(solid)@C.T*SCALE;z0=float(solid[:,2].min());z1=float(solid[:,2].max());sections=[]
    for a,b in zip(np.linspace(z0,z1,9)[:-1],np.linspace(z0,z1,9)[1:]):
        p=solid[(solid[:,2]>=a-1e-5)&(solid[:,2]<=b+1e-5)];assert len(p)
        radius=float(np.linalg.norm(p[:,:2],axis=1).max());sections.append([float(a),float(b),radius])
    pivot=(PIVOT@C.T*SCALE).tolist();tip=[pivot[0],pivot[1],pivot[2]+z1];muzzle=pivot
    profile='IRIS_DRILL 2 8 19\n'+' '.join('%.9f'%v for v in [LENGTH,.416666667,1.633333333,3.75,4,5.216666667,5.633333333,*pivot,15,4.125])+ '\n'+'\n'.join(' '.join('%.9f'%v for v in row) for row in sections)+'\n'
    # 同一源网格顺序生成绑定名；与运行时逐层绑定和离线mesh核对保持合同。
    profile+=''.join(str(i)+' '+material(x)+'\n' for i,x in enumerate(drill))
    put(ASSET/'drill.csv',profile,'动作/部件/查询合同','八段轴向胶囊保守包络从实体顶点拟合；排除四张装饰光学面，当前不伤害')
    for name,p in TEXTURES.items():put(ASSET/name,p.read_bytes(),'源武器纹理','保留实际DDS字节，纠正作者绝对路径为本包局部引用')
    im=Image.new('RGBA',(1,1),(255,255,255,255));buf=BytesIO();im.save(buf,format='DDS');put(ASSET/'iris_white.dds',buf.getvalue(),'无发光纹理缺省','仅缺少glow槽时取白图并由源emission=0关闭发光')
    lines=[]
    for name,d in MATERIALS.items():
        emit=' '.join('%.9f'%v for v in d['emission']);uv=' '.join('%.9f'%v for v in d['uv_offset']+d['uv_scale'])
        lines.append('material '+name+'\n{\n technique\n {\n  pass\n  {\n   lighting off\n   depth_check on\n   depth_write '+('off' if d['optical'] else 'on')+'\n   cull_hardware none\n   scene_blend '+('add' if d['optical'] else 'alpha_blend')+'\n   vertex_program_ref Basic_Texture_VP {}\n   fragment_program_ref IrisArsenal_FP\n   {\n    param_named emission float3 '+emit+'\n    param_named uvTransform float4 '+uv+'\n   }\n   texture_unit { texture '+d['diffuse']+' }\n   texture_unit { texture '+d['glow']+' }\n  }\n }\n}\n')
    lines.append('''
material IrisArsenal/Debug
{
 technique
 {
  pass
  {
   lighting off
   depth_check off
   depth_write off
   scene_blend alpha_blend
   vertex_program_ref Basic_Coloured_Texture_VP {}
   fragment_program_ref IrisArsenalDebug_FP {}
   texture_unit { texture iris_white.dds }
  }
 }
}
''')
    put(ASSET/'iris.material','\n'.join(lines),'源材质适配','实际diffuse/glow、源发光颜色、UV与alpha；不沿用艾芙尼尔绿色')
    put(ASSET/'iris.program','fragment_program IrisArsenal_FP hlsl\n{\n source iris.hlsl\n entry_point iris_fp\n target ps_4_0\n}\nfragment_program IrisArsenalDebug_FP hlsl\n{\n source iris.hlsl\n entry_point iris_debug_fp\n target ps_4_0\n}\n','Ogre程序声明','使用已验证Basic_Texture_VP输入，不新增Renderable基类转换')
    put(ASSET/'iris.hlsl','// Basic_Texture_VP的实际输出合同；normal装备不读取未提供的custom参数。\nstruct Input {float4 pos:SV_Position;float4 colour:COLOR;float4 uv:TEXCOORD0;};\nTexture2D diffuseTex:register(t0);Texture2D glowTex:register(t1);\nSamplerState diffuseSampler:register(s0);SamplerState glowSampler:register(s1);\nfloat4 iris_fp(Input i,uniform float3 emission,uniform float4 uvTransform):SV_Target {\n float2 uv=i.uv.xy*uvTransform.zw+uvTransform.xy;\n float4 base=diffuseTex.Sample(diffuseSampler,uv);float3 glow=glowTex.Sample(glowSampler,uv).rgb;\n return float4(base.rgb+glow*emission,base.a);\n}\n// 调试顶点色独立于源材质。\nfloat4 iris_debug_fp(Input i):SV_Target {return i.colour;}\n','前向源发光着色器','按实际发光图和参数恢复纹理；无自定义参数/粒子工厂')
    # 模型投影图仅用于检查形体、轴向和源资产，不宣称游戏实机渲染。
    image=Image.new('RGB',(960,480),(24,27,34));draw=ImageDraw.Draw(image)
    for points,offset,color in [(npnt,100,(240,170,50)),(dp,540,(255,110,30))]:
        p=points[:,[2,0]] if offset==540 else npnt[:,[1,0]];lo=p.min(0);hi=p.max(0);q=(p-lo)/(hi-lo).max()*340
        for x,y in q[::max(1,len(q)//18000)]:draw.point((offset+x,420-y),fill=color)
    buf=BytesIO();image.save(buf,format='PNG');put(ROOT/'docs/source-geometry-preview.png',buf.getvalue(),'普通枪/钻头形体投影','仅源模型点云与包围可视核对，不冒充实机效果')
    icon=Image.new('RGBA',(640,128),(0,0,0,0));idraw=ImageDraw.Draw(icon);allp=npnt[:,[1,0]];lo=allp.min(0);hi=allp.max(0);k=min(620/(hi[0]-lo[0]),112/(hi[1]-lo[1]))
    center=(lo+hi)*.5
    for x in normal:
        points=(np.array(x['vertices'])@x['matrix'][:3,:3].T+x['matrix'][:3,3])@C.T@R.T*SCALE
        xy=(points[:,[1,0]]-center)*[k,-k]+[320,64]
        source_texture=texture(x['textures'][0]);image_tex=Image.open(TEXTURES[source_texture]).convert('RGB')
        for tri in x['triangles']:
            uv=np.mean(np.array(x['uv'])[tri],axis=0)%1;color=image_tex.getpixel((int(uv[0]*(image_tex.width-1)),int(uv[1]*(image_tex.height-1))))
            idraw.polygon([tuple(xy[i]) for i in tri],fill=(*color,255))
    buf=BytesIO();icon.save(buf,format='PNG');put(ASSET/'iris_weapon_icon.png',buf.getvalue(),'真实武器图标','实际源网格/纹理投影，避免自动图标只看见一条线')
    put(ROOT/'docs/asset-provenance.json',json.dumps({'model_scale':SCALE,'normal_source':str(SOURCE/'Meshes/SW/Iris/2.nif'),'drill_source':str(SOURCE/'Meshes/SW/Iris/EXDrill1.nif'),'source_controller':{'node':'TwinChakrams','frequency':15,'phase':0,'start':0,'stop':4.125,'rotation_y_key_times':[0,2.041666746,4.125],'rotation_y_key_values':[0,math.pi,2*math.pi]},'source_pivot':PIVOT.tolist(),'muzzle_local':muzzle,'tip_local_full':tip,'capsules':sections,'normal_bounds':[npnt.min(0).tolist(),npnt.max(0).tolist()],'drill_bounds':[dp.min(0).tolist(),dp.max(0).tolist()],'adaptation':'仅附加钻头轴向展开/收回包络为原型适配；旋转/几何/纹理来自源。四张源光学面不参与碰撞。','unresolved':'胶囊是显式保守代理，不是逐三角精确接触；实机握持/渲染/查询待验收'},ensure_ascii=False,indent=2),'资产和碰撞来源','记录统一坐标、真实旋转、尺寸以及代理精度边界')

def records(p):
    b=p.read_bytes();i=fcs.find_records_start(b);out=[]
    while i<len(b):r=fcs.read_record(b,i,len(b));out.append(r);i=r['end']
    assert i==len(b);return out

def field(r,name,kind,value):
    n=['bool','f32','long','vec3','vec4','string','filename'].index(kind);raw=fcs.w_str(value) if kind in ['string','filename'] else struct.pack('<'+{'bool':'?','f32':'f','long':'i'}[kind],value)
    r['sections'][n]=[(a,k,v) for a,k,v in r['sections'][n] if a!=name]+[(name,kind,raw)]
def blank(t,i,n):return {'type':t,'id':0,'key':str(i)+'-IrisArsenal.mod','name':n,'save':0,'sections':[[] for _ in range(7)],'cats':[],'inst':b'\0'*4}
def refs(name,rows):return fcs.w_str(name)+fcs.put(len(rows))+b''.join(fcs.w_str(k)+struct.pack('<3i',*v) for k,*v in rows)
def mod_assets():
    base=records(GAME/'data/rebirth.mod');weapon=copy.deepcopy(next(x for x in base if x['type']==2 and x['name']=='Naginata'));weapon.update(id=0,key='1-IrisArsenal.mod',name='伊莉丝·锤枪（钻头验证）')
    for name in ['cut damage multiplier','blunt damage multiplier','pierce damage multiplier','min cut damage mult']:field(weapon,name,'f32',0)
    for name,value in [('length',18),('inventory footprint width',10),('inventory footprint height',2),('value',1)]:field(weapon,name,'long',value)
    for name in ['mesh','bare sword','ground mesh']:field(weapon,name,'filename','./mods/IrisArsenal/assets/iris_weapon.mesh')
    # 后续原型重建也保持正式武器分类，避免回退成长柄刀；值取本机原生重武器。
    field(weapon,'skill category','long',3);field(weapon,'skill category animation override','long',21)
    field(weapon,'description','string','无伤害工程验证：正常锤枪→钻头展开旋转→收回。只允许本武器私有动作；碰撞仅记录。');field(weapon,'auto icon image','bool',False);field(weapon,'icon','filename','./mods/IrisArsenal/assets/iris_weapon_icon.png')
    # 047原生武器图标读取bare sword相机；同一校准同时覆盖初始生成和后续完整重建。
    import icon_camera;icon_camera.apply(weapon,field)
    anim=blank(112,2,'IrisArsenal drill proof animations');field(anim,'preprocess','bool',True)
    for sex in ['male','female']:field(anim,sex+' animation','filename','./mods/IrisArsenal/assets/iris_drill_'+sex+'.skeleton')
    tech=blank(17,3,'IrisArsenal Drill Proof')
    for name in ['1 handed','blunt','gains ground','hackers','heavy weapons','is block','is dodge','is prone','is stumble dodge','katanas','low strike','sabre','unarmed']:field(tech,name,'bool',False)
    field(tech,'polearm','bool',False);field(tech,'heavy weapons','bool',True);field(tech,'disabled','bool',True);field(tech,'anim name','string',ANIM)
    for name,value in [('acceptable end time',99.5),('anim blocked frame 1',90),('anim stop frame 1',99),('anim hesitate point',0),('anim speed mult',1),('attack distance',36),('attack distance min vs static',0),('chance',0),('max encumbrance',999),('max skill',999),('min skill',0),('num frames',100)]:field(tech,name,'f32',value)
    for name,value in [('animal',0),('attack direction 1',0),('limb 1',0),('max simultaneous hits',0),('num techniques',1),('power 1',0)]:field(tech,name,'long',value)
    out=[weapon,anim,tech]
    # 本体不写入任何种族覆盖；种族动画接入仅由独立兼容补丁负责。
    # 禁止再从原版／其他工程的种族名单回填，避免清理后完整重建又恢复覆盖。
    # 复制原版研究但使用本mod新ID时，必须清除低4位修改／改名标记，不能把新研究当作不存在的覆盖。
    research=copy.deepcopy(next(r for r in base if r['type']==21 and r['name']=='Naginatas'));research.update(id=0,key='4-IrisArsenal.mod',name='伊莉丝锤枪·验证原型');research['save']&=~15;research['cats']=[refs('enable weapon type',[('1-IrisArsenal.mod',0,0,0)]),refs('requirements',[('52323-rebirth.mod',0,0,0)])];out.append(research)
    header=struct.pack('<I',1)+b''.join(fcs.w_str(s) for s in ['Codex','IrisArsenal 0.1.0：钻头闭环工程验证；无伤害；需要RE_Kenshi。','',''])+b'\0'*10
    data=struct.pack('<II',17,len(header))+header+struct.pack('<II',100,len(out))+b''.join(fcs.write_record(r) for r in out)
    put(OUT/'IrisArsenal.mod',data,'隔离FCS武器/技巧/动画','私有chance0/disabled；本武器无伤害，原生动作只保留收尾')
    assert fcs.roundtrip(str(OUT/'IrisArsenal.mod'))['identical']
    put(ROOT/'docs/fcs-records.json',json.dumps([{'id':r['key'],'type':r['type'],'name':r['name']} for r in out],ensure_ascii=False,indent=2),'FCS身份清单','记录测试获取ID，不改存档/商店/其他武器')

def main():
    # 已升级八招的项目禁止误跑旧闭环main覆盖FCS/动画；保留其纯读取/拟合工具供新作者复用。
    if (ROOT/'docs/eight-moves.json').exists():raise RuntimeError('八招项目请运行tools/author_moves.py及tools/author_effects.py；旧闭环作者不得覆盖新包')
    visual_assets();body_assets();mod_assets()
    sources=[HKX,SKEL,SOURCE/'Meshes/SW/Iris/2.nif',SOURCE/'Meshes/SW/Iris/EXdrill.nif',SOURCE/'Meshes/SW/Iris/EXDrill1.nif',SOURCE/'SKSE/PayloadInterpreter/Config/Iris.ini']
    put(ROOT/'docs/source-hashes.json',json.dumps({str(p):sha(p) for p in sources},ensure_ascii=False,indent=2),'源只读身份','固定源动画/参考骨架/模型/事件配置')
    # 完整资产重新制作时最后再应用源金属/alpha与BC7兼容层，防止旧简化材质覆盖本轮修复。
    from prepare_drill_optics import prepare
    prepare()
if __name__=='__main__':main()
