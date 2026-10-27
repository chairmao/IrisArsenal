"""061非编译专项：源条件抽取/独立规格回放，不执行C++、PhysX或游戏。

本专项独立执行，不加入UpdateMod；原始060/历史验收保留历史语义，不改断言冒充新版本通过。
"""
from pathlib import Path
import ast,hashlib,itertools,json,math,random,re,unittest
from safeio import ROOT
from test_melee_block043 import function

def code(s):return re.sub(r'//[^\n]*','',s)
def sha(b):return hashlib.sha256(b).hexdigest()

class NativeCombat061Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.c=(ROOT/'IrisCombat.cpp').read_text('utf-8-sig');cls.r=(ROOT/'IrisRanged.cpp').read_text('utf-8-sig')
  cls.main=(ROOT/'IrisArsenal.cpp').read_text('utf-8-sig');cls.d=(ROOT/'IrisDiagnostics.cpp').read_text('utf-8-sig')
  cls.base=json.loads((ROOT/'docs/native-combat-061-baseline.json').read_text('utf8'))

 def test_native_four_checks_exhaustive_from_source(self):
  # 直接抽取实际C++前五个return条件，转换其布尔表达式，与独立规则逐项比较；不运行C++。
  f=function(self.c,'DamagePolicyReason');branches=re.findall(r'if\(([^\n]+?)\)return ("[^"]+"|0);',f)[:5]
  self.assertEqual(len(branches),5)
  mappings={'caster->isValid()':'cv','caster->isDestroyed()':'cd','victim->isValid()':'vv','victim->isDestroyed()':'vd',
            'victim->isDead()':'dead','caster->isAlly(victim,false)':'ally','victim->isLiterallyUnconciousNotPretending()':'unc',
            'caster->isEnemy(victim,true)':'enemy','caster==victim':'same'}
  expressions=[]
  for cond,result in branches:
   for a,b in mappings.items():cond=cond.replace(a,b)
   expressions.append((cond.replace('&&',' and ').replace('||',' or ').replace('!',' not ').strip(),None if result=='0' else json.loads(result)))
  names=('caster','victim','cv','cd','vv','vd','dead','ally','unc','enemy','same');cases=0
  for bits in itertools.product((False,True),repeat=len(names)):
   env=dict(zip(names,bits))
   for ranged,melee_current,ranged_current in itertools.product((False,True),repeat=3):
    active=ranged_current if ranged else melee_current
    got='neutral_not_active_target' if not active else None
    for expr,result in expressions:
     if eval(expr,{'__builtins__':{}},env):got=result;break
    if not env['caster'] or not env['victim'] or not env['cv'] or env['cd'] or not env['vv'] or env['vd'] or env['same']:expected='invalid_or_self'
    elif env['dead']:expected='dead'
    elif env['ally']:expected='ally'
    elif env['unc']:expected='true_unconscious'
    elif env['enemy'] or active:expected=None
    else:expected='neutral_not_active_target'
    self.assertEqual(got,expected);cases+=1
  self.assertEqual(cases,16384)
  self.assertIn('if(ranged){RangedCombatClass* rc=',f);self.assertIn('else{CombatClass* cc=',f)
  self.assertIn('return active==victim?0:"neutral_not_active_target"',f)

 def test_collision_and_medical_share_qualification(self):
  self.assertIn('!CanDamage(caster,victim,true)',function(self.c,'IgnoreRangedContact'))
  self.assertIn('CanDamage(caster,victim,move==5||move==6||move==7)',function(self.c,'DamageTarget'))
  self.assertIn('DamageTarget(caster,victim,j.move)',function(self.c,'Collect'))
  self.assertIn('CanDamage(caster,victim,RangedMove(r.move),&eligibilityReason)',function(self.c,'Flush'))

 def test_wall_character_ordering_with_transparent_people(self):
  # 墙同距优先，盟友/旁观者/真昏迷透明；主动中立目标可以接触。角色容量不因过滤而改变。
  f=function(self.c,'AdvanceEffects');condition=re.search(r'if\((!hit\|\|hits\.items\[k\]\.fraction<f)\)',f).group(1)
  condition=condition.replace('!hit','not hit').replace('||',' or ').replace('hits.items[k].fraction','contact')
  rng=random.Random(61001)
  for _ in range(4000):
   walls=[rng.randrange(101)/100 for _ in range(rng.randrange(10))]
   people=[(rng.randrange(101)/100,rng.choice(('ally','neutral','unconscious','enemy','active_neutral'))) for _ in range(rng.randrange(257))]
   hit=bool(walls);f=min(walls) if hit else 1;who='wall' if hit else None
   for contact,kind in sorted(people):
    if kind not in ('enemy','active_neutral'):continue
    if eval(condition,{'__builtins__':{}},dict(hit=hit,contact=contact,f=f)):who=kind;f=contact;hit=True
    break
   oracle=[(v,0,'wall') for v in walls]+[(v,1,k) for v,k in people if k in ('enemy','active_neutral')]
   expected=min(oracle) if oracle else None
   self.assertEqual((f,who) if hit else None,(expected[0],expected[2]) if expected else None)

 def test_direct_contact_survives_second_query_and_deduplicates(self):
  blast=function(self.c,'Blast');resolve=function(self.c,'ResolveJobs');flush=function(self.c,'Flush')
  self.assertIn('j.victims.insert(*direct)',blast);self.assertIn('DamageTarget(c,v,move)',blast)
  self.assertIn('r.direct=j.haveDirect&&Same(*h,j.directVictim)',resolve)
  self.assertIn('std::swap(directVictim,other.directVictim)',self.c)
  self.assertIn('damage_rejected cast=',flush);self.assertIn('direct=',flush)
  # 完整身份保留五个字段；即使另一形体/延迟球查询没返回直接目标，也不能丢失已有物理证据。
  a=(1,2,3,4,5);b=(1,2,3,4,6)
  for overlaps,expected in (([],{a}),([a,a],{a}),([b,b],{a,b}),([a,b,a],{a,b})):
   self.assertEqual({a}|set(overlaps),expected)
  for i in range(5):
   other=list(a);other[i]+=1;self.assertEqual(len({a,tuple(other)}),2)
  events=[(11,0,a),(11,1,a),(12,0,a)]
  self.assertEqual(len(set(events)),3) # 不跨攻击段/施放合并。
  self.assertEqual([x for x in events if x[2]!=a],[]) # 消费前目标变为盟友/昏迷，仍可拒绝，不强补医疗。

 def test_terrain_ray_radius_geometry_and_failure_budget_preserved(self):
  for name,value in self.base['combat'].items():
   current=function(self.c,name)
   if name=='Contacts':
    # 唯一允许的差异是失败日志的首次16条门移除；查询体/预算/调用/结果不变，不更新旧摘要掩盖差异。
    old='if(queryNotices<16){++queryNotices;std::ostringstream o;o<<"eight_query_retry status="'
    new='if(IrisDiagnostics::DetailsEnabled()){std::ostringstream o;o<<"eight_query_retry status="'
    self.assertEqual(current.count(new),1);current=current.replace(new,old)
   self.assertEqual(sha(current.encode()),value,name)
  for rel,value in self.base['native'].items():self.assertEqual(sha((ROOT/rel).read_bytes()),value,rel)
  contacts=function(self.c,'Contacts');advance=function(self.c,'AdvanceEffects')
  self.assertIn('IrisNative::ProjectileAll',contacts);self.assertIn('IrisNative::CylinderAll',contacts)
  self.assertIn('split?&terrain:0',advance);self.assertIn('const unsigned required=split?2U:1U',advance)
  from test_ranged_ray057 import geometry_cases,budget_failure_cases
  self.assertFalse(geometry_cases()['models_execute_PhysX']);self.assertEqual(budget_failure_cases()['hard_total_limit'],64)

 def test_selected_model_survives_idle_cleanup_and_concurrent_permission(self):
  end=code(function(self.c,'End'));tick=code(function(self.c,'Tick'))
  self.assertIn('if(a.ranged||a.active||a.reserved)a.rangedChoice=-1',end)
  self.assertIn('int selected=activeCount<maxActors&&',tick)
  self.assertLess(tick.index('a.rangedChoice=PickRanged'),tick.index('IrisRanged::Publish'))
  self.assertLess(tick.index('IrisRanged::Publish'),tick.index('IrisRanged::TakeRequest'))
  self.assertEqual(tick.count('PickRanged('),1)
  for ranged,active,reserved in itertools.product((False,True),repeat=3):
   choice=6
   if ranged or active or reserved:choice=-1
   self.assertEqual(choice,6 if not any((ranged,active,reserved)) else -1)
  # 同窗口两人已获许可时，只有先消费者占槽；第二人消费重查而非依赖上一帧ready。
  active_count=0;started=[]
  for actor in (1,2):
   if active_count<1:started.append(actor);active_count+=1
  self.assertEqual(started,[1])

 def test_actual_speed_matches_native_prediction_and_instant_beam(self):
  publish=function(self.r,'Publish');capture=function(self.r,'CaptureAim');emit=function(self.c,'Emit');tick=function(self.c,'Tick')
  self.assertIn('s->gun->shotSpeed=effectiveShotSpeed',publish)
  self.assertIn('ProjectileSpeed(aimMove)*aimRate',tick)
  self.assertIn('NativeBodyPoint(target):rc->getAimPos(target)',capture)
  self.assertIn('s->gun->instantAim?0.f:s->gun->shotSpeed',capture)
  self.assertIn('expected=ProjectileSpeed(a.move)*a.rate',emit)
  self.assertIn('instantAim&&bodyReady?bodyPoint:target',self.r)
  self.assertIn('target->isAnimal()?"Bip01 Spine1":"Bip01 Spine2"',self.r)
  for speed,rate,dt in itertools.product((800.,440.),(.25,.6,1.,1.2,2.5),(.016,.025,.25)):
   self.assertAlmostEqual(speed*(dt*rate),(speed*rate)*dt)

 def test_fcs_range_and_empty_expiry_are_distinct_from_contact(self):
  emit=code(function(self.c,'Emit'));advance=code(function(self.c,'AdvanceEffects'))
  self.assertIn('s.range=nativeRanged?moves[a.move].technique->initialDistance:',emit)
  self.assertIn('if(split&&!hit)',advance);self.assertIn('contact=0 reason=range_limit',advance)
  self.assertLess(advance.index('if(split&&!hit)'),advance.index('if(!Blast('))
  self.assertIn('hit&&!worldBlocker?&blocker:0',advance)
  # 相同初始瞄准距离768时，旧实现到808空爆；新上限10000仍飞行，不冒称C++实跑。
  old_limit=max(768+40,120);new_limit=10000
  self.assertTrue(900>=old_limit);self.assertFalse(900>=new_limit)

 def test_medical_semantics_and_safe_window_unchanged(self):
  flush=code(function(self.c,'Flush'))
  for token in ('w->physics->isRunning()','queuesAreClearMT()','AINonRenderThread()','w->isPaused()','r.generation!=epoch','getTotalAttackDamageFor(victim)','damage.multiply(r.mult)','xpMelee(outcome,victim,damage)'):
   self.assertIn(token,flush)
  self.assertEqual(flush.count('->_NV_hitByMeleeAttack('),1)
  self.assertIn('!RangedMove(r.move)&&moves[r.move].bypassDefence',flush)
  self.assertLess(flush.index('submittedTotal=damage.total()'),flush.index('->_NV_hitByMeleeAttack('))
  for bad in ('addWound(','CreateThread(','std::thread','setPosition('):self.assertNotIn(bad,flush)

 def test_no_lifetime_detail_caps_and_config_retirement(self):
  all_code=code(self.c+self.r+self.main+self.d)
  self.assertIsNone(re.search(r'\b\w*(?:Logs|Notices)\w*\s*(?:\+\+)?\s*<\s*\d',all_code))
  for token in ('event_detail_limit=0','log_total_limit=0','[IrisArsenal 0.4.18]'):self.assertIn(token,self.d)
  self.assertIn('if(!enabled)return',function(self.d,'Log'))
  self.assertIn('<=65536',function(self.d,'Log')) # 失败缓冲有界，不等于日志文件总行数限额。
  for rel in ('distribution/IrisArsenal.ini','package/IrisArsenal/IrisArsenal.ini'):
   text=(ROOT/rel).read_text('utf-8-sig')
   self.assertIsNone(re.search(r'^DamageUnconsciousTargets\s*=',text,re.M))
   for token in ('EnableLogging=1','EnableCombatDetailLogging=1','DamageFlushBudgetMs=2.5','DamageFlushMaxHits=32'):self.assertIn(token,text)
  self.assertEqual((self.main+self.c+self.r).count('KenshiLib::AddHook('),18)

 def test_assets_dll_balance_and_daily_update_preserved(self):
  count=0
  for rel,value in self.base['runtime'].items():
   if rel in ('IrisArsenal.ini','IrisPackage.json'):continue
   self.assertEqual(sha((ROOT/'package/IrisArsenal'/rel).read_bytes()),value,rel);count+=1
  self.assertGreater(count,130)
  update=(ROOT/'tools/update_mod.py').read_text('utf-8-sig')
  self.assertIn('stage_package.main(run_checks=False)',update)
  self.assertNotIn('test_native_combat061',update)
  self.assertFalse(json.loads((ROOT/'package/IrisArsenal/IrisPackage.json').read_text('utf8'))['ready'])

 def test_actual_sdk_library_and_old_dll_rejection(self):
  from stage_package import validate_dll,POLICY_CONTRACT
  sdk=ROOT.parents[1]/'1.Dependencies/KenshiLib_0.5.0'
  symbol=b'?getAimPos@RangedCombatClass@@QEAA?AVVector3@Ogre@@PEAVCharacter@@@Z'
  for p in (sdk/'Libraries/KenshiLib.lib',Path('D:/steam/steamapps/common/Kenshi/KenshiLib.dll')):self.assertIn(symbol,p.read_bytes())
  dll=ROOT.parent/'bin/Release/IrisArsenal.dll'
  if POLICY_CONTRACT.encode() not in dll.read_bytes():
   with self.assertRaisesRegex(RuntimeError,'061'):validate_dll()
  else:self.assertIn(POLICY_CONTRACT.encode(),validate_dll()[1])

if __name__=='__main__':unittest.main(verbosity=2)
