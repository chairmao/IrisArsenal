"""060专项：真实源码/资产合同核验，不编译，不把静态检查称为游戏实测。"""
from pathlib import Path
import json,hashlib,unittest
from safeio import ROOT
from test_melee_block043 import function
class SharedAimTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.c=(ROOT/'IrisCombat.cpp').read_text('utf8');cls.r=(ROOT/'IrisRanged.cpp').read_text('utf8');cls.h=(ROOT/'IrisRanged.h').read_text('utf8')
  cls.base=json.loads((ROOT/'docs/shared-aim-060-baseline.json').read_text('utf8'))
 def test_actual_muzzle_unchanged_and_forwarded_without_offsets(self):
  # 实际枪口公式及Tick发布路径逐字节保持；CaptureAim仅原样赋值，不引入头部/根位置偏移。
  f=function(self.r,'CaptureAim');emit=function(self.c,'Emit')
  self.assertIn('Vector3 muzzle=Muzzle(weapon)+a.origin;',emit)
  self.assertIn('CaptureAim(c,muzzle,rangedAim)',emit)
  for token in ('s->gun->barrel=muzzle','s->gun->position=muzzle','s->aim.muzzle=muzzle'):self.assertIn(token,f)
  for token in ('muzzle+','muzzle +','getBoneWorldPosition(', 'getPosition(', 'setPosition(', 'setOrientation('):self.assertNotIn(token,f)
 def test_same_native_point_and_direction(self):
  capture=function(self.r,'CaptureAim');emit=function(self.c,'Emit')
  self.assertIn('s->aim.point=rc->currentAimPos',capture)
  self.assertIn('AimDirection(muzzle,s->aim.point)',capture)
  self.assertIn('getAimDir(const Vector3& target){return AimDirection(barrel,target);}',self.r)
  drive=emit[emit.index('}else if(e.kind==8){'):emit.index('}else if(e.kind==0){')]
  self.assertIn('target=rangedAim.point,d=rangedAim.direction',drive);self.assertNotIn('Target(',drive)
  self.assertIn('else if(nativeRanged){s.target=rangedAim.point;aim=nativeEvidence;}',emit)
  self.assertIn('if(nativeRanged)s.direction=rangedAim.direction',emit)
  self.assertIn('Path(muzzle,muzzle+d*reach,e.radius,false,true)',drive)
 def test_protected_combat_and_native_hooks_unchanged(self):
  sha=lambda b:hashlib.sha256(b).hexdigest()
  for name,value in self.base['combat'].items():self.assertEqual(sha(function(self.c,name).encode()),value,name)
  for name,value in self.base['ranged'].items():self.assertEqual(sha(function(self.r,name).encode()),value,name)
  self.assertEqual(self.r.count('KenshiLib::AddHook('),8)
 def test_no_extra_queries_or_native_timing_calls(self):
  capture=function(self.r,'CaptureAim');direction=function(self.r,'AimDirection')
  for token in ('takeTheShotCheck(', 'getAimPos(', 'lookatPosition(', 'CreateThread(', 'EnterCriticalSection(', 'raycast', 'linearCapsuleSweep', 'resetShotTimer(', 'reloadCheck('):self.assertNotIn(token,capture+direction)
  frame=self.h.split('struct AimFrame {',1)[1].split('};',1)[0]
  for token in ('Character*','SceneNode*','NxShape*','NxActor*'):self.assertNotIn(token,frame)
 def test_target_loss_cache_is_bounded_to_active_action(self):
  f=function(self.r,'CaptureAim');self.assertIn('if(!s->busy||!s->haveAim)return false',f)
  self.assertIn('last_native_currentAimPos',f);self.assertIn('s->haveAim=false',function(self.r,'Finish'))
  self.assertIn('delete i->second',function(self.r,'Reset'))
  self.assertIn('!Iris::Finite(rc->currentAimPos)',f)
 def test_all_runtime_assets_and_existing_dll_preserved(self):
  for name,value in self.base['runtime'].items():self.assertEqual(hashlib.sha256((ROOT/'package/IrisArsenal'/name).read_bytes()).hexdigest(),value,name)
 def test_old_dll_is_rejected_by_new_contract(self):
  from stage_package import validate_dll,AIM_CONTRACT
  dll=ROOT.parent/'bin/Release/IrisArsenal.dll'
  if AIM_CONTRACT.encode() not in dll.read_bytes():
   with self.assertRaisesRegex(RuntimeError,'060'):validate_dll()
  else:self.assertIn(AIM_CONTRACT.encode(),validate_dll()[1])
if __name__=='__main__':unittest.main(verbosity=2)
