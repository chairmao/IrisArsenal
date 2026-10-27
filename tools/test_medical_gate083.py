"""083非编译验收：实际医疗门AST与FIFO/重入状态规格；不执行游戏或PhysX。"""
from pathlib import Path
from types import SimpleNamespace as NS
import argparse,ast,hashlib,itertools,json,re,sys
ROOT=Path(__file__).resolve().parents[1]
from test_window_audit082 import GateProgram,gate_text,wrapper,run,disabled_paths,trace_specs
from test_performance080 import Program

def condition_case(source,bits):
 wp,pp,initialized,reset,loading,running,clear,ap,ar,paused=bits
 trace=[]
 def call(name,value):
  def f():trace.append(name);return value
  return f
 ai=NS(isRunning=call('ai.isRunning',ar)) if ap else None
 phy=NS(isRunning=call('physics.isRunning',running),queuesAreClearMT=call('queuesAreClearMT',clear)) if pp else None
 w=NS(physics=phy,initialized=initialized,gameResetting=reset,isLoadingFromASaveGame=call('isLoadingFromASaveGame',loading),AINonRenderThread=call('AINonRenderThread',ai),isPaused=call('isPaused',paused)) if wp else None
 snap=NS(reason='unset',gateCause='unset',gateAt=0,gate=None)
 def state():return NS(physicsRunning=-1,queuesClear=-1,aiRunning=-1,paused=-1,unavailable=-1,failed=False)
 p,body=wrapper(gate_text(source));run(p,body,{'w':w,'now':100,'queueSnapshot':snap,'IrisDiagnostics::WindowState':state})
 return snap,trace

def gates(old,new):
 count=unblocked=0
 for bits in itertools.product((False,True),repeat=10):
  wp,pp,initialized,reset,loading,running,clear,ap,ar,paused=bits
  a,ta=condition_case(old,bits);b,tb=condition_case(new,bits)
  expected='world_missing' if not(wp and pp) or not initialized or reset or loading else 'physics_busy' if running else 'ai_busy' if ap and ar else 'paused' if paused else 'allowed'
  assert b.reason==expected,(bits,vars(b),tb)
  assert 'queuesAreClearMT' not in tb and b.gate.queuesClear==-1
  if b.reason=='allowed' and not clear:
   assert a.reason=='physics_busy' and a.gateCause=='queues_not_clear';unblocked+=1
  if b.reason=='physics_busy':assert b.gateCause=='physics_running'
  count+=1
 assert unblocked>0
 return dict(actual_AST_cases=count,previously_blocked_idle_cases_allowed=unblocked,medical_queue_getter_calls=0)

def tokens(text):
 p=Program('void Check(){'+text+'}');return p.tokens(p.body('Check'))

def function_map(source):
 p=Program(source);result={}
 for n in p.nodes('function_definition'):
  body=n.child_by_field_name('body');header=' '.join(p.source[n.start_byte:body.start_byte].decode().split());parents=[];cur=n.parent
  while cur:
   if cur.type in ('struct_specifier','class_specifier','namespace_definition'):
    name=cur.child_by_field_name('name')
    if name:parents.append(p.txt(name))
   cur=cur.parent
  key='::'.join(reversed(parents))+' / '+header;assert key not in result,key;result[key]=p.tokens(body)
 return result

def protected(before,c,d):
 old=(before/'IrisCombat.cpp').read_text('utf-8-sig');a=function_map(c);b=function_map(old);assert set(a)==set(b)
 changed=[k for k in a if a[k]!=b[k]]
 assert len(changed)==3 and all(any(x in k for x in ('Configure(','Flush(','~DamageQueueSnapshot(')) for k in changed),changed
 # 仅把医疗许可前缀复原到旧值，整个伤害消费体（预算、FIFO、epoch、敌我、受击、经验、结果）须逐token相同。
 p,q=Program(c),Program(old);new=p.txt(p.body('Flush'));prev=q.txt(q.body('Flush'))
 start=new.index('queueSnapshot.gate=IrisDiagnostics::WindowState()');end=new.index('Hurt r;{Guard guard;',start)
 os=prev.index('queueSnapshot.gate=IrisDiagnostics::WindowState()');oe=prev.index('Hurt r;{Guard guard;',os)
 assert tokens(new[:start]+prev[os:oe]+new[end:])==tokens(prev)
 # Configure只允许083启动日志及其政策字段变化；不改INI默认值或数值加载。
 cfg=p.txt(p.body('Configure'));oldcfg=q.txt(q.body('Configure'))
 cfg=re.sub(r'\{std::ostringstream out;out<<"medical_gate_ready contract=IRIS_MEDICAL_GATE_083.*?Log\(out.str\(\)\);\}','',cfg)
 cfg=cfg.replace('medical_policy=split_gate_083','medical_policy=unchanged');assert tokens(cfg)==tokens(oldcfg)
 od=(before/'IrisDiagnostics.cpp').read_text('utf-8-sig');x,y=Program(re.sub(r'__declspec\((?:[^()]|\([^()]*\))*\)','',d)),Program(re.sub(r'__declspec\((?:[^()]|\([^()]*\))*\)','',od))
 for name in ('ObserveWindow','SnapshotWaits','RecordWait','Now','ResetWindowAudit','BeginWindowAudit','WindowAuditHasWork','WindowAuditEnabled','PerformanceEnabled','DetailsEnabled'):
  current_map,old_map=function_map(x.source.decode()),function_map(y.source.decode())
  pick=lambda m:next(v for k,v in m.items() if re.search(r' / (?:static )?(?:void|bool|double) '+re.escape(name)+r'\(',k))
  assert pick(current_map)==pick(old_map),name
 # 所有引擎Hook及真实PhysX/角色半径/环境射线实现须原字节不变。
 for name in ('IrisArsenal.cpp','IrisCombat.h','IrisRanged.cpp','IrisRanged.h','IrisDiagnostics.h','native/NativeMultiContact.cpp','native/NativeMultiContact.h','native/FiniteCylinder.h'):
  assert (ROOT/name).read_bytes()==(before/name).read_bytes(),name
 return dict(combat_unchanged_function_count=len(a)-len(changed),intentional_changed_functions=changed,medical_body_except_gate_identical=True,configure_values_identical=True,protected_diagnostic_functions=10,hook_and_query_files_unchanged=8)

def ready_cases(d):
 p=GateProgram(re.sub(r'__declspec\((?:[^()]|\([^()]*\))*\)','',d))
 fn=next(n for n in p.nodes('function_definition') if 'void Add(const WindowState& s,double cost,bool requireQueues)' in p.txt(n).split('{')[0]);body=fn.child_by_field_name('body')
 branch=next(n for n in body.named_children if n.type=='if_statement' and '++ready' in p.txt(n))
 count=0
 for unavailable,physics,queue,ai,paused,failed,required in itertools.product((-1,0,1),(-1,0,1),(-1,0,1),(-1,0,1),(-1,0,1),(False,True),(False,True)):
  s=NS(unavailable=unavailable,physicsRunning=physics,queuesClear=queue,aiRunning=ai,paused=paused,failed=failed)
  expected=not failed and unavailable==0 and physics==0 and (not required or queue==1) and ai==0 and paused==0
  assert bool(p.expr(branch.child_by_field_name('condition'),dict(s=s,requireQueues=required)))==expected;count+=1
 assert 'const bool requireQueues=phase!=WINDOW_MEDICAL;' in d
 return count

def replay(c):
 normal=(True,True,True,False,False,False,False,True,False,False)
 def gate(bits):return condition_case(c,bits)[0].reason
 # 每轮每笔执行实际AST医疗门；纯值队列/重入事件是规格模型，不伪称原生线程测试。
 scenarios={
  'physics_starts':(5,True),'AI_starts':(8,True),'pause':(9,True),
  'world_reset':(3,True),'loading':(4,True),'world_uninitialized':(2,False),'physics_missing':(1,False)}
 for name,(index,value) in scenarios.items():
  queue=list(range(100));applied=[];state=list(normal)
  assert gate(state)=='allowed';applied.append(queue.pop(0));state[index]=value
  assert gate(state)!='allowed' and queue[0]==1,name
  state=list(normal)
  while queue:
   for _ in range(32):
    if not queue:break
    assert gate(state)=='allowed';applied.append(queue.pop(0))
  assert applied==list(range(100)) and len(set(applied))==100,name
 # 时间预算在请求间检查，不抢占/重放已经执行的原生受击；下一窗口仍从原FIFO头继续。
 queue=list(range(102));applied=[];windows=[]
 while queue:
  elapsed=0;done=0;start=len(applied)
  while queue and done<32:
   if done and elapsed>=2.5:break
   assert gate(normal)=='allowed'
   item=queue.pop(0);applied.append(item);elapsed+=3.5 if item==0 else .25;done+=1
  windows.append(applied[start:])
 assert windows[0]==[0] and windows[1][0]==1 and applied==list(range(102))
 # 实际epoch判定表达式：Clear已经改变代次时，旧请求不得进入受击。
 p=Program(c);b=p.body('Flush');conditions=[]
 def visit(n):
  if n.type=='if_statement' and 'r.generation!=epoch' in p.txt(n.child_by_field_name('condition')):conditions.append(n.child_by_field_name('condition'))
  for x in n.named_children:visit(x)
 visit(b);assert len(conditions)==1
 for a,e in itertools.product(range(3),repeat=2):assert bool(p.expr(conditions[0],dict(r=NS(generation=a),epoch=e)))==(a!=e)
 return dict(reentrant_transition_scenarios=len(scenarios),FIFO_targets_per_scenario=100,slow_call_and_time_budget_targets=102,epoch_expression_cases=9,native_calls_or_threads_executed=False)

def main(before,out):
 c=(ROOT/'IrisCombat.cpp').read_text('utf-8-sig');old=(before/'IrisCombat.cpp').read_text('utf-8-sig');d=(ROOT/'IrisDiagnostics.cpp').read_text('utf-8-sig');a=(ROOT/'IrisArsenal.cpp').read_text('utf-8-sig')
 result=dict(actual_gate=gates(old,c),protected=protected(before,c,d),diagnostic_ready_AST_cases=ready_cases(d),logging_disabled_actual_paths=disabled_paths(a,d),retained_window_trace_specs=trace_specs(d),replay=replay(c))
 from test_capsule_policy081 import check_shadow,check_storage,check_geometry
 n=(ROOT/'native/NativeMultiContact.cpp').read_text('utf-8-sig');result['retained081']=dict(shadow_cases=check_shadow(c),storage=check_storage(n),geometry=check_geometry(n))
 syntax=[]
 for file in list(ROOT.glob('*.cpp'))+list(ROOT.glob('*.h'))+list((ROOT/'native').glob('*.cpp'))+list((ROOT/'native').glob('*.h')):
  Program(re.sub(r'__declspec\((?:[^()]|\([^()]*\))*\)','',file.read_text('utf-8-sig')));syntax.append(file.relative_to(ROOT).as_posix())
 for name in ('tools/stage_package.py','tools/test_medical_gate083.py','tools/test_update_mod.py'):ast.parse((ROOT/name).read_text('utf-8-sig'))
 from stage_package import validate_dll
 try:validate_dll()
 except RuntimeError as e:assert '083医疗安全门修复' in str(e);result['old_user_DLL_rejected']=str(e)
 else:raise AssertionError('旧082 DLL不得冒充083')
 result.update(syntax_checked=syntax,compiled=False,game_tested=False,FPS_measured=False)
 with out.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);p.add_argument('--out',type=Path,required=True);v=p.parse_args();main(v.before,v.out)