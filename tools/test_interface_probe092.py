"""092非编译验收：实际接口树/试验门AST、原消费者和同输入两策略结果，不冒充实机。"""
from pathlib import Path
from types import SimpleNamespace as NS
import argparse,ast,configparser,itertools,json,math,random,re,sys,copy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from test_work_trace091 import VM as BaseVM,normal
from test_performance080 import Program,Returned
from test_native_profile084 import definitions,free_body
from test_medical_gate083 import replay
class Env(dict):
 def __init__(self,obj,other):
  self.obj=obj;self.fields=set(vars(obj));super().__init__(vars(obj));self.update(other)
 def __setitem__(self,k,v):
  super().__setitem__(k,v)
  if k in self.fields:setattr(self.obj,k,v)
class VM(BaseVM):
 def expr(self,n,e):
  if n.type=='assignment_expression':
   l=n.child_by_field_name('left');r=n.child_by_field_name('right');op=self.source[l.end_byte:r.start_byte].decode().strip()
   v=self.expr(r,e)
   if op=='+=':v=self.expr(l,e)+v
   elif op=='-=':v=self.expr(l,e)-v
   else:assert op=='='
   self.assign(l,e,v);return v
  if n.type=='binary_expression':
   l=n.child_by_field_name('left');r=n.child_by_field_name('right');op=self.source[l.end_byte:r.start_byte].decode().strip()
   if op=='&':return self.expr(l,e)&self.expr(r,e)
  if n.type=='switch_statement':
   value=self.expr(n.child_by_field_name('condition'),e);body=n.child_by_field_name('body');matched=False
   for case in body.named_children:
    if case.type=='comment':continue
    if case.type!='case_statement':raise AssertionError(case.type)
    label=case.child_by_field_name('value')
    if label is None or self.expr(label,e)==value:matched=True
    if not matched:continue
    for stmt in case.named_children:
     if stmt==label:continue
     if stmt.type=='break_statement':return None
     self.statement(stmt,e)
   return None
  return super().expr(n,e)
 def statement(self,n,e):
  if n.type=='else_clause':return self.statement(n.named_children[0],e)
  if n.type=='switch_statement':self.expr(n,e);return
  if n.type=='declaration' and self.txt(n).startswith('Guard guard'):
   e.get('observed',[]).append('lock');return
  return super().statement(n,e)
def text(p):return p.read_text('utf8')
def strip(s):
 s=normal(s);p=Program(s);erase=[];variables=[]
 for n in p.nodes('declaration'):
  if re.match(r'IrisDiagnostics::(?:InterfaceScope|CombatInterfaceFrame)\s+',p.txt(n)):
   variables+=re.findall(r'IrisDiagnostics::(?:InterfaceScope|CombatInterfaceFrame)\s+(\w+)',p.txt(n));erase.append((n.start_byte,n.end_byte))
 for n in p.nodes('if_statement'):
  if p.txt(n.child_by_field_name('condition'))=='(probeCost)':erase.append((n.start_byte,n.end_byte))
 b=p.source
 for a,z in sorted(erase,reverse=True):b=b[:a]+b[z:]
 s=b.decode()
 for var in set(variables):s=re.sub(r'\b'+var+r'\.(?:Switch|Finish)\([^;]*\);','',s)
 s=s.replace('IrisDiagnostics::ResetCombatInterfaceAudit();','')
 s=re.sub(r'unsigned probeArm=2;policy.single=IrisDiagnostics::SelectRangedSingleProbe\([\s\S]*?,probeArm\);','',s)
 s=re.sub(r'IrisDiagnostics::RangedProbeSample probeSample=\{0\};const bool probeCost=IrisDiagnostics::RangedProbeCostEnabled\(\);','',s)
 s=re.sub(r'IrisDiagnostics::Scope timing\(IrisDiagnostics::(RANGED_\w+),0,&audit\.\w+\);',r'IrisDiagnostics::Scope timing(IrisDiagnostics::\1);',s)
 return s
def preserve(before):
 total=0;files={}
 for f in ['IrisArsenal.cpp','IrisCombat.cpp','native/NativeMultiContact.cpp']:
  old=text(before/f);new=text(ROOT/f);a,b=Program(normal(old)),Program(strip(new));count=0
  assert old.count('__fastcall')==new.count('__fastcall'),f
  for n in a.nodes('function_definition'):
   body=n.child_by_field_name('body');header=a.source[n.start_byte:body.start_byte].decode()
   found=[m.child_by_field_name('body') for m in b.nodes('function_definition') if b.source[m.start_byte:m.child_by_field_name('body').start_byte].decode()==header]
   assert found and any(a.tokens(body)==b.tokens(x) for x in found),(f,header)
   count+=1
  files[f]=count;total+=count
 for f in ['IrisRanged.cpp','IrisRanged.h','IrisNativeAudit.cpp','IrisNativeAudit.h','IrisWoundAudit.cpp','IrisWoundAudit.h','IrisCombat.h']:
  assert (before/f).read_bytes()==(ROOT/f).read_bytes(),f
 return dict(original_functions=total,per_file=files,original_calling_conventions=True,ABI_hooks_and_medical_untouched=True)
def part_names(h):
 return [x.strip() for x in re.search(r'enum InterfacePart \{([^}]+)\}',h)[1].split(',') if x.strip()!='IF_PART_COUNT']
def interface_cases(d,h):
 p=VM(normal(d));names=part_names(h);count=len(names)
 bodies={}
 for name in ['Begin','Finish','Switch','FromKind']:
  found=[n.child_by_field_name('body') for n in p.nodes('function_definition') if 'InterfaceScope::'+name+'(' in p.source[n.start_byte:n.child_by_field_name('body').start_byte].decode()]
  assert len(found)==1; bodies[name]=found[0]
 rootctor=definitions(p,'CombatInterfaceFrame');rootdtor=definitions(p,'CombatInterfaceFrame',True)
 class Stat:
  def __init__(self):self.values=[];self.maxCall=0
  def Sample(self,v):self.values.append(v);self.maxCall=max(self.maxCall,v)
  def Frame(self,v):pass
 def stats():return NS(total=Stat(),inclusive=[Stat() for _ in names],exclusive=[Stat() for _ in names],
   calls=[0]*count,maxCall=[0.]*count,invalid=0,nested=0,exceptions=0)
 cases=0;closed=0;disabled=0;rng=random.Random(92043)
 for enabled,reset,exception in itertools.product([False,True],repeat=3):
  for scenario in range(36):
   observed=[];tls=[None];clock=[100.];epoch=[1];run,window=stats(),stats()
   def now():observed.append('clock');clock[0]+=.025;return clock[0]
   def gettls():observed.append('tls_read');return tls[0]
   def settls(v):observed.append('tls_write');tls[0]=v;return True
   def parent():return enabled
   consts={name:i for i,name in enumerate(names)}
   consts.update(IF_PART_COUNT=count,COMBAT_TICK=1000,SPHERE_QUERY=1001,SWEEP_QUERY=1002,CAPSULE_QUERY=1003,CYLINDER_QUERY=1004,CAPSULE_BATCH_QUERY=1005,
    NATIVE_TERRAIN_RAY=1006,NATIVE_SPHERE_SWEEP=1007,RANGED_BATCH_QUERY=1008,RESOURCE_GROUP=1009,VISUAL_CREATE=1010,MATERIAL_LOAD=1011,ASSET_READ=1012,
    PREWARM=1013,VISUAL_UPDATE=1014,ATTACHMENT_UPDATE=1015,TRAIL_UPDATE=1016,PATH_BUILD=1017,QUERY_JOBS=1018,CONTACT_COLLECT=1019,DAMAGE_ENQUEUE=1020)
   base=dict(consts,InterfaceEnabled=parent,interfaceOption=enabled,InterfaceTLSRead=gettls,InterfaceTLSWrite=settls,
    GetLastError=lambda:55,SetLastError=lambda v:observed.append(('error',v)),Now=now,InterfaceGeneration=lambda:epoch[0],frameId=9,
    observed=observed,_finite=math.isfinite,**{'std::max':max,'std::uncaught_exception':lambda:exception},
    interfaceRun=run,interfaceWindow=window,interfaceSlowMs=10000,interfaceNotices=0,lastInterfaceSlow=0)
   root=NS(active=False,sealed=False,generation=0,nested=0,badClocks=0,token=0,begin=0.,endedAt=0.,
      inclusive=[None]*count,exclusive=[None]*count,maxCall=[None]*count,calls=[None]*count,top=None)
   env=Env(root,dict(base,this=root));p.run(rootctor,env)
   def scope():return NS(frame=None,boundary=None,previous=None,part=0,begin=0.,children=0.)
   boundary=scope()
   def method(obj,name,**args):
    extra=dict(base,this=obj,**args)
    extra['Finish']=lambda at=0:method(obj,'Finish',at=at)
    extra['Begin']=lambda value,at=0:method(obj,'Begin',value=value,at=at)
    return p.run(bodies[name],Env(obj,extra))
   method(boundary,'FromKind',value=1000,at=100.)
   if enabled and scenario==0:
    nested=copy.deepcopy(root);nested.active=False
    p.run(rootctor,Env(nested,dict(base,this=nested)))
    assert not nested.active and tls[0] is root and root.nested==1
    p.run(rootdtor,Env(nested,dict(base,this=nested)));assert tls[0] is root
    second=scope();method(second,'FromKind',value=1000,at=100.001);assert not second.boundary
    method(second,'Finish',at=100.002);assert not root.sealed
   stack=[]
   for j in range(scenario%9+1):
    obj=scope();method(obj,'Begin',value=1+rng.randrange(count-1),at=clock[0]);stack.append(obj)
    clock[0]+=.01
    if j%3==1:
     method(obj,'Switch',value=names.index('IF_SHOT_CONSUME'))
     assert not enabled or root.top is obj
    if j%2==0:
     top=stack.pop();method(top,'Finish',at=clock[0])
   while stack:
    top=stack.pop();clock[0]+=.01;method(top,'Finish',at=clock[0])
   if enabled and scenario==0:
    mappings={'SPHERE_QUERY':'IF_PHYSICS','SWEEP_QUERY':'IF_PHYSICS','CAPSULE_QUERY':'IF_PHYSICS','CYLINDER_QUERY':'IF_PHYSICS',
      'CAPSULE_BATCH_QUERY':'IF_PHYSICS','NATIVE_TERRAIN_RAY':'IF_PHYSICS','NATIVE_SPHERE_SWEEP':'IF_PHYSICS','RANGED_BATCH_QUERY':'IF_PHYSICS',
      'RESOURCE_GROUP':'IF_RESOURCE','VISUAL_CREATE':'IF_RESOURCE','MATERIAL_LOAD':'IF_RESOURCE','ASSET_READ':'IF_RESOURCE',
      'PREWARM':'IF_PREWARM','VISUAL_UPDATE':'IF_VISUAL','ATTACHMENT_UPDATE':'IF_ATTACHMENTS','TRAIL_UPDATE':'IF_TRAIL',
      'PATH_BUILD':'IF_BLADE_PATH','QUERY_JOBS':'IF_JOBS','CONTACT_COLLECT':'IF_COLLECT','DAMAGE_ENQUEUE':'IF_ENQUEUE'}
    for kind,part in mappings.items():
     observed_scope=scope();method(observed_scope,'FromKind',value=consts[kind],at=clock[0])
     assert observed_scope.frame is root and observed_scope.part==consts[part],(kind,part,observed_scope.part)
     clock[0]+=.001;method(observed_scope,'Finish',at=clock[0])
   # 原父Scope已有结束值；封口后的接口不可再读时钟/写本根。
   end=clock[0]+1.;method(boundary,'Finish',at=end)
   if enabled:
    assert root.sealed and root.endedAt==end and root.top is None
    before_obs=len(observed);after=scope();method(after,'Begin',value=1,at=0)
    assert after.frame is None and 'clock' not in observed[before_obs:]
   if reset:epoch[0]+=1
   p.run(rootdtor,Env(root,dict(base,this=root)))
   if not enabled:
    assert not observed;disabled+=1
   elif reset:
    assert run.invalid==window.invalid==1 and not run.total.values
   else:
    assert len(run.total.values)==1 and math.isclose(sum(run.exclusive[i].values[0] for i in range(count)),end-100.,abs_tol=1e-9)
    assert run.exceptions==int(exception) and not tls[0];closed+=1
   cases+=1
 return dict(actual_tree_AST_scenarios=cases,closed_same_parent_roots=closed,disabled_no_TLS_clock_lock=disabled,parts=count,
             reentry_reset_discarded=True,exception_unwind=True,sealed_root_rejects_late_scopes=True)
def experiment_cases(d):
 p=VM(normal(d));select=definitions(p,'SelectRangedSingleProbe');cost=free_body(p,'RangedProbeCostEnabled')
 cases=0;atomic=0
 for configured,eligible,ab,logging,cost_option in itertools.product([False,True],repeat=5):
  seq=[0]
  def inc(_):seq[0]+=1;return seq[0]
  for i in range(14):
   e=dict(configured=configured,eligible=eligible,probeABOption=ab,probeCostOption=cost_option,probeTrialSequence=0,arm=99,unsigned=int,
      InterlockedIncrement=inc,DetailsEnabled=lambda:logging)
   e['RangedProbeCostEnabled']=lambda e=e:p.run(cost,e)
   result=p.run(select,e);on=all([configured,eligible,ab,logging,cost_option])
   assert e['arm']==((i%2) if on else 2)
   assert result==(i%2==1 if on else configured)
   assert seq[0]==(i+1 if on else 0)
   atomic+=int(on);cases+=1
 return dict(actual_select_AST_cases=cases,alternates_without_replay=True,disabled_no_atomic=True,enabled_assignments=atomic)
def existing_scope_clock_cases(d):
 p=VM(normal(d));ctor=definitions(p,'Scope');dtor=definitions(p,'Scope',True);cases=0
 header=next(p.source[n.start_byte:n.child_by_field_name('body').start_byte].decode() for n in p.nodes('function_definition') if 'Scope::Scope(' in p.source[n.start_byte:n.child_by_field_name('body').start_byte].decode())
 expression=header.split('active(',1)[1].split('),accumulate(',1)[0]
 gate=VM('bool Gate(){return '+expression+';}');gatebody=definitions(gate,'Gate')
 class Pointer:
  def __init__(self):self.value=0.
 class TimerVM(VM):
  def expr(self,n,e):
   if n.type=='pointer_expression' and self.txt(n).startswith('*'):
    return self.expr(n.named_children[-1],e).value
   return super().expr(n,e)
  def assign(self,n,e,v):
   if n.type=='pointer_expression':
    self.expr(n.named_children[-1],e).value=v;return
   return super().assign(n,e,v)
 p=TimerVM(normal(d));ctor=definitions(p,'Scope');dtor=definitions(p,'Scope',True)
 for old_active,cost_enabled,has_output,force_interface in itertools.product([False,True],repeat=4):
  seen=[];clock=iter([100.,103.]);pointer=Pointer() if has_output else None
  def now():seen.append('clock');return next(clock)
  enabled=gate.run(gatebody,dict(value=9,accumulatedMs=pointer,Active=lambda _:old_active,RangedProbeCostEnabled=lambda:cost_enabled,**{'InterfaceScope::ClockNeeded':lambda _:force_interface}))
  part=NS(FromKind=lambda *x:seen.append(('bind',x)),Finish=lambda *x:seen.append(('finish',x)))
  e=dict(value=9,kind=9,label=None,active=enabled,begin=0.,accumulate=pointer,interfacePart=part,
   Now=now,ResourceKind=lambda _:False,Record=lambda *v:seen.append(('record',v)),**{'std::max':max})
  p.run(ctor,e);p.run(dtor,e)
  assert seen.count('clock')==2*int(enabled)
  assert pointer is None or pointer.value==(3. if enabled else 0.)
  assert [v for v in seen if isinstance(v,tuple) and v[0]=='bind']==([('bind',(9,100.))] if enabled else [])
  assert [v for v in seen if isinstance(v,tuple) and v[0]=='finish']==([('finish',(103.,))] if enabled else [])
  cases+=1
 return dict(actual_Scope_AST_cases=cases,accumulator_reuses_original_two_clocks=True,disabled_zero_clock=True,parent_end_forwarded_exactly=True)

def main(before,out):
 d=text(ROOT/'IrisDiagnostics.cpp');h=text(ROOT/'IrisDiagnostics.h')
 result=dict(preserved=preserve(before),interface_tree=interface_cases(d,h),probe_experiment=experiment_cases(d),reused_scope_clocks=existing_scope_clock_cases(d))
 c=strip(text(ROOT/'IrisCombat.cpp'));result['medical_FIFO_specs']=replay(re.sub(r'workTrace\.Mark\([^;]+\);','',c))
 syntax=[]
 for f in list(ROOT.glob('*.cpp'))+list(ROOT.glob('*.h'))+list((ROOT/'native').glob('*.cpp'))+list((ROOT/'native').glob('*.h')):
  s=normal(text(f));s=re.sub(r'typedef Item\*\(RootObjectFactory::\* CreateMember\)\([^;]+;','typedef void* CreateMember;',s);Program(s);syntax.append(str(f.relative_to(ROOT)))
 assert len(re.findall(r'"[^"]+"',re.search(r'interfaceNames\[IF_PART_COUNT\]=\{([^}]+)\}',d)[1]))==len(part_names(h))
 for f in ['distribution/IrisArsenal.ini','package/IrisArsenal/IrisArsenal.ini']:
  ini=configparser.ConfigParser();ini.read(ROOT/f,encoding='utf8')
  assert all(ini['IrisArsenal'][k]=='1' for k in ['EnableCombatInterfaceProfiling','EnableRangedProbeCostLogging','EnableRangedSingleProbeABTest'])
  assert ini['IrisArsenal']['DamageFlushMaxHits']=='32' and ini['IrisArsenal']['DamageFlushBudgetMs']=='2.5'
 for f in ['tools/stage_package.py','tools/test_update_mod.py',__file__]:ast.parse(text(Path(f) if f==__file__ else ROOT/f))
 from stage_package import validate_dll
 try:validate_dll()
 except RuntimeError as e:assert '092全量接口和宽相成本监视' in str(e);result['actual_old_DLL_rejected']=str(e)
 else:raise AssertionError('091产物不能冒充092')
 result.update(grammar_units=syntax,compiled=False,real_Windows_TLS_PhysX_threads_game=False,FPS_measured=False)
 out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);p.add_argument('--out',type=Path,required=True);x=p.parse_args();main(x.before,x.out)
