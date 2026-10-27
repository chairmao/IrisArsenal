"""059源PA10/真实准星/枪口蓝火/闭合R9光流的非编译专项；不冒称PhysX或GPU执行。"""
import json,hashlib,zipfile,math,re
from pathlib import Path
import numpy as np
from safeio import ROOT
from effect_data059 import buffers,curves
from test_melee_block043 import function
from verify_moves import body_check
import scene_geometry as g,port_math as m
A=ROOT/'package/IrisArsenal/assets'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify_drive059():
 moves=json.loads((ROOT/'docs/eight-moves.json').read_text('utf8'))['moves'];spec=moves[7];C=(ROOT/'IrisCombat.cpp').read_text('utf8');e=json.loads((ROOT/'docs/drive059-assets.json').read_text('utf8'));fx=json.loads((ROOT/'docs/eight-effects.json').read_text('utf8'))
 assert spec['key']=='drive' and spec['duration']==5.5 and spec['frames']==331
 assert len(spec['sources'])==1 and Path(spec['sources'][0]).name=='mco_powerattack10.hkx'
 assert all(sha(path)==digest for path,digest in spec['source_hashes'].items())
 assert not any(k in spec for k in ('seat049','seat050','height047'))
 assert len(spec['events'])==4 and all(x['kind']=='beam' and x['radius']==9 for x in spec['events'])
 np.testing.assert_allclose([x['time'] for x in spec['events']],3.1665399074554443+np.arange(4)*.25,atol=1e-8)
 assert [spec['attack_min'],spec['attack_max']]==[0,10000]
 # 读取序列化男女骨架和独立握点证明，固定骨长/肩持水平轴，不能凭作者自报图像判断。
 poses=[]
 for sex in ('male','female'):
  body_check(spec,sex,A/f'iris_action_drive_{sex}.skeleton');ids,frames,bones=g.actual_frames(A/f'iris_action_drive_{sex}.skeleton',spec)
  native=m.skeleton(Path('D:/steam/steamapps/common/Kenshi/data/character/meshes')/f'{sex}_skeleton/{sex}_skeleton.skeleton')
  assert all(np.allclose(b['position'],n['position']) for b,n in zip(bones,native))
  for ev in spec['events']:
   pose=frames[round(ev['time']/spec['duration']*(spec['frames']-1))];grip,q=pose[ids['Bip01 Prop2']];q=m.qmul(q,m.axis((1,0,0),-90));axis=np.asarray(m.rotate(q,[0,0,1]));left=np.asarray(grip)+m.rotate(q,[1.807138657,-.35,3.0]);err=np.linalg.norm(np.asarray(pose[ids['Bip01 L Hand']][0])-left);shoulder=np.asarray(pose[ids['Bip01 R UpperArm']][0]);muzzle=np.asarray(grip)+m.rotate(q,[1.807138657,0,8.534358047])
   assert axis@[0,0,1]>.99 and err<.002,(sex,ev,axis,err)
   assert abs(muzzle[1]-shoulder[1])<4,(sex,muzzle,shoulder)
   poses.append({'sex':sex,'time':ev['time'],'axis':axis.tolist(),'left_grip_error':float(err),'muzzle_y':float(muzzle[1]),'shoulder_y':float(shoulder[1])})
 # 原始180准星顶点/两组与九炮片，不用旧截图重画环；真实源纹理按原PNG字节读取。
 assert len(e['parts'])==11 and sum(p['vertices'] for p in e['parts'] if p['role']=='reticle_blue')==180
 assert sorted(p['vertices'] for p in e['parts'] if p['role']=='reticle_blue')==[36,144]
 assert e['blue_sha256']==sha(e['blue_source']) and np.allclose(e['blue_phase'],[3.1665399074554443,3.7265399074554444])
 assert e['fire_phase'][0]==e['blue_phase'][1] and e['fire_phase'][1]==5.5
 raw=buffers(A/'iris_fx_ion.mesh');states,dur,_=curves(A/'effect_curves.csv','ion');assert len(raw)==len(states)<33 and dur==5.5
 reticles=[i for i,(name,_) in enumerate(raw) if '/Reticle' in name];assert len(reticles)==2
 for i in reticles:
  mat=states[i,:,13:].reshape(-1,3,4);norm=np.linalg.norm(mat[:,:,:3],axis=1)[:,0];assert norm.min()<.43 and norm.max()>.99
  # 相邻采样的旋转不能在蓄力结束突然归零；以矩阵的连续性检出旧snap错误。
  assert np.linalg.norm(np.diff(mat[:,:,:3],axis=0),axis=(1,2)).max()<.3
  assert np.ptp(mat[:20,0,1])>.1
 blue=[i for i,(n,_) in enumerate(raw) if '/Blue/' in n];assert blue
 ts=np.linspace(0,dur,states.shape[1]);assert all(np.all(states[i,ts<e['blue_phase'][0],3]==0) and np.all(states[i,ts>=e['blue_phase'][1],3]==0) for i in blue)
 # 外部CC0源图逐字节相等；三层闭合柱几何没有旧金环或球形尖头伸过墙后。
 z=zipfile.ZipFile(ROOT/'tools/source-cache/drive059/beamvfxassets.zip')
 for source,target in [('Laser1.png','iris_drive059_laser.png'),('FlamesTexture.png','iris_drive059_flow.png')]:assert z.read('BeamVFXAssets/'+source)==(A/target).read_bytes()
 parts=g.mesh(A/'iris_fx_beam.mesh');assert len(parts)==3
 for part,r in zip(parts,(1,.72,.32)):
  p=part['p'];assert len(p)==1757 and abs(np.linalg.norm(p[:,:2],axis=1).max()-r)<1e-6
  assert p[:,2].min()==0 and p[:,2].max()==1
  triangles=p[part['tri']];caps=np.ptp(triangles[:,:,2],axis=1)==0;assert caps.sum()==128
 # 恢复旧版目标瞄准：方向源为目标身体减炮口；查询和可视仍消费同一快照，不修改其他安全链。
 emit=function(C,'Emit');branch=emit[emit.index('}else if(e.kind==8){'):emit.index('}else if(e.kind==0){')]
 for token in ('Target(c,a.aim,&aim)','d=target-muzzle','!Finite(d)','d.normalise()','muzzle+d*reach,e.radius,false,true','technique->initialDistance','DRIVE_REBUILD_CONTRACT','aim_mode=target_body'):assert token in branch
 assert not any(token in branch for token in ('weapon[0][2]','weapon[1][2]','weapon[2][2]'))
 show=function(C,'ShowParts');assert 'a.ion.Draw(w,t,1.f)' in show and '.383318f' not in show and 't>=1.70f' not in show
 assert 'Vector3(r.radius,r.radius,r.length)' in function(C,'DrawBeam')
 preserved=json.loads((ROOT/'docs/drive059-preserved.json').read_text('utf8'))
 # 历史不变量只约束未改动资源；DLL/安装清单是本次组包产物，不能要求它们等于旧版本。
 # 当前DLL仍由stage_package.validate_dll独立检查PE、059合同与源码时间，不放宽版本正确性。
 protected_runtime={rel:digest for rel,digest in preserved['runtime'].items() if rel not in ('IrisArsenal.dll','IrisPackage.json')}
 for rel,digest in protected_runtime.items():assert sha(ROOT/'package/IrisArsenal'/rel)==digest,rel
 for name,digest in preserved['combat_functions'].items():assert hashlib.sha256(function(C,name).encode()).hexdigest()==digest,name
 for index,old in preserved['other_moves'].items():assert moves[int(index)]==old,index
 assert all(sha(ROOT/rel)==digest for rel,digest in preserved['native_and_ranged'].items())
 # 专用程序声明/参数必须从真实源码找到；该检查不能代替HLSL编译。
 code=(A/'iris_drive059.hlsl').read_text('utf8');program=(A/'iris_drive059.program').read_text('utf8');material=(A/'iris_drive059.material').read_text('utf8')
 assert 'source iris_drive059.hlsl' in program and 'clock.w/36' in code and 'clock.x*(7+layer.x*2)' in code
 assert material.count('IrisDriveStreamFP')==3 and material.count('IrisDriveMountFP')==11
 assert (ROOT/'package/IrisArsenal/CREDITS-drive059.txt').is_file()
 from stage_package import BUILD_CONTRACT,validate_dll
 assert BUILD_CONTRACT=='IRIS_DRIVE_REBUILD_059'
 dll=ROOT.parent/'bin/Release/IrisArsenal.dll'
 if BUILD_CONTRACT.encode() not in dll.read_bytes():
  try:validate_dll()
  except RuntimeError as error:assert '059' in str(error)
  else:raise AssertionError('旧DLL混用059资源')
 return {'source_clip':'PA10','poses':poses,'source_reticle_vertices':180,'source_red_reticle_parts':9,'beam_radius':9,'beam_length':10000,'health_pulses':4,'aim_mode':'target_body_each_pulse','CC0_textures_exact':True,'other_nine_specs_exact':True,'unchanged_runtime_files':len(protected_runtime),'protected_combat_functions':len(preserved['combat_functions']),'new_hooks':0,'new_threads':0,'compiled':False,'GPU_tested':False,'game_tested':False}
if __name__=='__main__':print(json.dumps(verify_drive059(),ensure_ascii=False,indent=2))
