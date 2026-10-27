"""082非编译验收：实际C++安全门AST、只读诊断边界及纯值重放；不执行C++/PhysX。"""
from pathlib import Path
from types import SimpleNamespace as NS
import argparse,ast,configparser,hashlib,itertools,json,random,re
from test_performance080 import Program
from test_native_melee072 import Returned
ROOT=Path(__file__).resolve().parents[1]
class GateProgram(Program):
 def expr(self,n,e):
  if n.type=='string_literal':return json.loads(self.txt(n))
  return super().expr(n,e)
def run(p,body,e):
 try:p.statement(body,e)
 except Returned:return e
 return e
def wrapper(text):
 p=GateProgram('void Check(){'+text+'}');return p,p.body('Check')
def overload(p,signature):
 matches=[n.child_by_field_name('body') for n in p.nodes('function_definition') if signature in p.source[n.start_byte:n.child_by_field_name('body').start_byte].decode()]
 assert len(matches)==1,(signature,len(matches));return matches[0]
def gate_text(c):
 start=c.index('queueSnapshot.gate=IrisDiagnostics::WindowState()') if 'queueSnapshot.gate=IrisDiagnostics::WindowState()' in c else c.index('if(!w||!w->physics){queueSnapshot.reason="world_missing"')
 end=c.index('Hurt r;{Guard guard;',start)
 prefix=c[start:end]
 pause=re.search(r'if\((?:paused|w->isPaused\(\))\)\{(?:queueSnapshot\.gateCause="paused";)?queueSnapshot\.reason="paused";return;\}',c[end:]).group()
 if 'if(paused)' in pause:prefix+='const bool paused=w->isPaused();queueSnapshot.gate.paused=paused?1:0;'
 return prefix+pause+'queueSnapshot.reason="allowed";'
def gates(old,new):
 op,ob=wrapper(gate_text(old));np,nb=wrapper(gate_text(new));cases=0
 for w_present,physics_present,running,clear,ai_present,ai_running,paused in itertools.product((False,True),repeat=7):
  traces=[];results=[]
  for p,body in ((op,ob),(np,nb)):
   trace=[]
   def call(name,value):
    def f():trace.append(name);return value
    return f
   ai=NS(isRunning=call('ai.isRunning',ai_running)) if ai_present else None
   phy=NS(isRunning=call('physics.isRunning',running),queuesAreClearMT=call('queuesAreClearMT',clear)) if physics_present else None
   w=NS(physics=phy,AINonRenderThread=call('AINonRenderThread',ai),isPaused=call('isPaused',paused)) if w_present else None
   snap=NS(reason='unset',gateCause='unset',gateAt=0,gate=None)
   def state():return NS(physicsRunning=-1,queuesClear=-1,aiRunning=-1,paused=-1,unavailable=-1,failed=False)
   e={'w':w,'now':100,'queueSnapshot':snap,'IrisDiagnostics::WindowState':state}
   run(p,body,e);traces.append(trace);results.append(snap)
  a,b=results;assert a.reason==b.reason and traces[0]==traces[1],(traces,vars(a),vars(b))
  if b.reason=='physics_busy':
   assert b.gateCause==('physics_running' if running else 'queues_not_clear')
   assert (b.gate.queuesClear==-1)==running
  cases+=1
 return cases

def protected(before,src):
 a=(ROOT/'IrisArsenal.cpp').read_text('utf-8-sig');oa=(before/'IrisArsenal.cpp').read_text('utf-8-sig')
 c=src;oc=(before/'IrisCombat.cpp').read_text('utf-8-sig')
 # 恢复唯一拆分的原短路块，再去掉所有诊断赋值；业务词法必须完整一致。
 p=Program(c);body=p.txt(p.body('Flush'));oldp=Program(oc);oldbody=oldp.txt(oldp.body('Flush'))
 first=body.index('queueSnapshot.gate=IrisDiagnostics::WindowState()');last=body.index('const double poppedAt',first)
 ostart=oldbody.index('if(!w||!w->physics){queueSnapshot.reason="world_missing"');oend=oldbody.index('const double poppedAt',ostart)
 body=body[:first]+oldbody[ostart:oend]+body[last:]
 body=re.sub(r'queueSnapshot\.gateCause=(?:"[^"]*"|queueSnapshot\.reason);','',body)
 x,y=wrapper(body),wrapper(oldbody);assert x[0].tokens(x[1])==y[0].tokens(y[1]),'Flush business tokens'
 # 既有原生调用顺序不变；SafeHook只允许新增局部诊断会话和Probe。
 p,q=Program(a),Program(oa);sa=p.txt(p.body('SafeHook'));so=q.txt(q.body('SafeHook'))
 sa=re.sub(r'WindowAuditSession windowAudit\(w\);|windowAudit\.Probe\(w,IrisDiagnostics::WINDOW_\w+\);','',sa)
 x,y=wrapper(sa),wrapper(so);assert x[0].tokens(x[1])==y[0].tokens(y[1]),'SafeHook business tokens'
 count=2
 for s,t,names in ((a,oa,['Idle','FrameHook','ChooseHook','NativeStandingMeleeAllowed']), (c,oc,['ResolveJobs','Collect','CanDamage','DamagePolicyReason','Choose','Emit','Blast','Tick','DamageOutcome','SlowNativeHit','ClearActor']), ((ROOT/'IrisDiagnostics.cpp').read_text('utf8'),(before/'IrisDiagnostics.cpp').read_text('utf8'),['ObserveWindow','SnapshotWaits','RecordWait'])):
  p,q=Program(re.sub(r'__declspec\((?:[^()]|\([^()]*\))*\)','',s)),Program(re.sub(r'__declspec\((?:[^()]|\([^()]*\))*\)','',t))
  for name in names:assert p.tokens(p.body(name))==q.tokens(q.body(name)),name;count+=1
 # Clear仅允许纯值诊断重置，不改变原来的事件/角色/后效清理。
 p,q=Program(c),Program(oc);clear=p.txt(overload(p,'void Clear(bool alive,const char* reason)'));clear=clear.replace('IrisDiagnostics::ResetWindowAudit();','');x,y=wrapper(clear),wrapper(q.txt(overload(q,'void Clear(bool alive,const char* reason)')));assert x[0].tokens(x[1])==y[0].tokens(y[1]);count+=1
 return count

def disabled_paths(a,d):
 # 实际四重开关表达式，以及Probe/入口的首个短路门；关闭不能访问引擎或调用QPC。
 d=re.sub(r'__declspec\((?:[^()]|\([^()]*\))*\)','',d);p=GateProgram(d)
 f=p.body('WindowAuditEnabled');cases=0
 for main,perf,detail,window in itertools.product((False,True),repeat=4):
  expr=f.named_children[0].named_children[0]
  assert p.expr(expr,{'windowAuditEnabled':window,'DetailsEnabled':lambda:main and perf and detail})==(main and perf and detail and window);cases+=1
 p=GateProgram(a);probe=overload(p,'void Probe(GameWorld* w,IrisDiagnostics::WindowPhase phase)');first=next(n for n in probe.named_children if n.type=='if_statement')
 for active,work in itertools.product((False,True),repeat=2):
  calls=[];e={'active':active,'IrisDiagnostics::WindowAuditHasWork':lambda:calls.append('work') or work}
  exits=False
  try:p.statement(first,e)
  except Returned:exits=True
  assert exits==(not(active and work))
  if not active:assert not calls
  cases+=1
 for name in ('WindowAuditHasWork','BeginWindowAudit','RecordWindowAudit','RecordMedicalWindow','FinishWindowAudit','ResetWindowAudit'):
  text=GateProgram(d).txt(GateProgram(d).body(name));assert text.index('WindowAuditEnabled()')<text.index('Guard guard'),name
 assert probe.start_byte<probe.end_byte and 'IrisDiagnostics::Now()' in p.txt(probe)
 return cases

def trace_specs(d):
 # 纯值日志规格；不假装执行原生锁/线程。未知字段、帧间隙、读档、限频和完整编码均覆盖。
 assert 'if(rejectStreak&&lastMedicalReject+1==windowSerial)' in d
 serial_last=0;streak=0;since=0;observed=[]
 for serial,now,blocked,reset in ((1,1000,True,False),(2,1020,True,False),(3,1040,False,False),(4,1060,True,False),(6,1100,True,False),(7,1120,True,True)):
  if reset:serial_last=streak=0;since=0
  if blocked:
   if streak and serial_last+1==serial:streak+=1
   else:streak=1;since=now
   serial_last=serial;observed.append((streak,now-since))
  else:serial_last=streak=0;since=0;observed.append((0,0))
 assert observed==[(1,0),(2,20),(0,0),(1,0),(1,0),(1,0)]
 # 首8不限频；其后同状态10秒、变化至少1秒。被抑制的明细不影响计数。
 def emit(n,elapsed,changed):return not(n>=8 and elapsed<10000 and (not changed or elapsed<1000))
 ratecases=0
 for n,elapsed,changed in itertools.product((0,7,8,100),(0,999,1000,9999,10000),(False,True)):
  expected=n<8 or elapsed>=10000 or changed and elapsed>=1000;assert emit(n,elapsed,changed)==expected;ratecases+=1
 rng=random.Random(82023)
 for _ in range(10000):
  values=[rng.choice((-1,0,1)) for _ in range(25)];s=sum((v+1)<<(i*2) for i,v in enumerate(values));assert [((s>>(i*2))&3)-1 for i in range(25)]==values
 assert 's.aiRunning==0&&s.paused==0' in d
 assert 'windowPeriod[p]=WindowStats()' in d and 'windowRun[p]=WindowStats()' not in d
 return {'streak_cases':len(observed),'rate_limit_cases':ratecases,'tri_state_roundtrips':10000}

def main(before):
 a=(ROOT/'IrisArsenal.cpp').read_text('utf8');c=(ROOT/'IrisCombat.cpp').read_text('utf8');d=(ROOT/'IrisDiagnostics.cpp').read_text('utf8');oc=(before/'IrisCombat.cpp').read_text('utf8')
 result={'actual_medical_gate_AST_cases':gates(oc,c),'business_function_token_checks':protected(before,c),'actual_logging_disabled_gate_cases':disabled_paths(a,d),'trace_specs':trace_specs(d)}
 for cfg in ('distribution/IrisArsenal.ini','package/IrisArsenal/IrisArsenal.ini'):
  old,new=configparser.ConfigParser(),configparser.ConfigParser();old.read(before/cfg,encoding='utf8');new.read(ROOT/cfg,encoding='utf8');assert new.getint('IrisArsenal','EnableWindowAuditLogging')==1
  new.remove_option('IrisArsenal','EnableWindowAuditLogging');assert {k:dict(old[k]) for k in old.sections()}=={k:dict(new[k]) for k in new.sections()}
 syntax=[]
 for file in list(ROOT.glob('*.cpp'))+list(ROOT.glob('*.h'))+list((ROOT/'native').glob('*.cpp'))+list((ROOT/'native').glob('*.h')):
  Program(re.sub(r'__declspec\((?:[^()]|\([^()]*\))*\)','',file.read_text('utf-8-sig')));syntax.append(str(file.relative_to(ROOT)))
 for f in ('tools/stage_package.py','tools/test_window_audit082.py'):ast.parse((ROOT/f).read_text('utf8'))
 # 081查询、去重和默认对照策略不受082诊断改动影响。
 from test_capsule_policy081 import check_shadow,check_storage,check_geometry
 n=(ROOT/'native/NativeMultiContact.cpp').read_text('utf8')
 result['retained081']={'shadow_cases':check_shadow(c),'storage':check_storage(n),'geometry':check_geometry(n)}
 # 检测数组只存纯值；阶段读取先判断工作量；原医疗没有新增引擎查询，阶段观察最多四点。
 assert 'if(!active||!IrisDiagnostics::WindowAuditHasWork())return;' in a
 assert 'WindowState windowStates[WINDOW_PHASE_COUNT]' in d and 'GameWorld*' not in d and 'NxShape*' not in d
 assert 'new_threads=0' in d and 'EnableWindowAuditLogging",false' in d
 result.update(syntax_checked=syntax,old_INI_values_preserved=True,medical_engine_call_order_preserved=True,additional_threads_or_hooks=False,compiled=False,real_thread_or_PhysX_executed=False,FPS_measured=False)
 return result
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--before',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);arg=parser.parse_args();result=main(arg.before)
 with arg.out.open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
 print(json.dumps(result,ensure_ascii=False,indent=2))
