"""090非编译验收：解释实际C++控制流；SDK用确定性值替身，不冒称真实PhysX/线程/游戏测试。"""
from pathlib import Path
from types import SimpleNamespace as NS
import argparse,copy,hashlib,itertools,json,math,random,re,struct,sys,configparser,ast
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from test_native_profile084 import Eval,definitions,free_body
from test_performance080 import Program,Returned
from test_medical_gate083 import replay
from test_ranged_work089 import VM as PriorVM
def f32(v):return struct.unpack('<f',struct.pack('<f',v))[0]
def norm(s):return re.sub(r'__declspec\((?:[^()]|\([^()]*\))*\)','',s)
def txt(p):return p.read_text('utf-8-sig')
class Break(Exception):pass
class Continue(Exception):pass
class Vec(list):
 x=property(lambda s:s[0],lambda s,v:s.__setitem__(0,v));y=property(lambda s:s[1],lambda s,v:s.__setitem__(1,v));z=property(lambda s:s[2],lambda s,v:s.__setitem__(2,v))
 def __init__(self,*v):super().__init__(v or (0.,0.,0.))
 def set(self,*v):self[:]=v
 def __truediv__(self,v):return Vec(*(a/v for a in self))
 def magnitude(self):return math.sqrt(sum(x*x for x in self))
class Box:
 def __init__(self):self.min=Vec();self.max=Vec()
 def setEmpty(self):self.min=Vec(math.inf,math.inf,math.inf);self.max=Vec(-math.inf,-math.inf,-math.inf)
 def combine(self,b):self.min=Vec(*(min(a,c) for a,c in zip(self.min,b.min)));self.max=Vec(*(max(a,c) for a,c in zip(self.max,b.max)))
class Diag(NS):pass
def diag(*a):return Diag(received=0,uniqueBeforeFailure=0,terrain=NS(groups=0,distance=-1))
def contacts(i):return NS(index=i,count=0,items=[],diagnostic=diag())
FIELDS='reused reuseFailed probeCalls probeCandidates probeCharacters probeUnknown probeException emptyPaths savedSweeps probeBusy probeHeadroom probeSparse probeSmall probeInvalid shadowChecks shadowMismatches'.split()
FIELDS+='spatialBatches spatialGroups spatialMerges spatialPairs spatialSingles spatialMultis spatialCovered spatialSkippedSingles spatialEmptySingles spatialEmptyMultis'.split()
class VM(Eval):
 def expr(self,n,e):
  k=n.type
  if k=='primitive_type':return {'float':f32,'double':float,'unsigned':int}[self.txt(n)]
  if k=='initializer_list':return [self.expr(a,e) for a in n.named_children]
  if k=='sizeof_expression':return 4
  if k=='cast_expression':return self.expr(n.child_by_field_name('value'),e)
  if k=='new_expression':
   typ=next(x for x in n.named_children if x.type=='type_identifier');args=[x for x in n.named_children if x.type=='argument_list'][-1]
   return e[self.txt(typ)](*[self.expr(a,e) for a in args.named_children])
  if k=='update_expression':
   a=n.named_children[0];old=self.expr(a,e);v=old+(-1 if '--' in self.txt(n) else 1);self.assign(a,e,v)
   return old if n.children[-1].type in ('++','--') else v
  if k=='assignment_expression':
   l=n.child_by_field_name('left');r=n.child_by_field_name('right');op=self.source[l.end_byte:r.start_byte].decode().strip();v=self.expr(r,e)
   if op=='+=':v=self.expr(l,e)+v
   elif op=='|=':v=self.expr(l,e)|v
   elif op=='-=':v=self.expr(l,e)-v
   else:assert op=='='
   self.assign(l,e,copy.deepcopy(v) if isinstance(v,(Diag,Box)) else v);return v
  if k=='binary_expression':
   l=n.child_by_field_name('left');r=n.child_by_field_name('right');op=self.source[l.end_byte:r.start_byte].decode().strip()
   if op in ('&','|','<<'):
    a,b=self.expr(l,e),self.expr(r,e);return {'&':lambda:a&b,'|':lambda:a|b,'<<':lambda:a<<b}[op]()
  if k=='call_expression':
   name=self.txt(n.child_by_field_name('function'));args=n.child_by_field_name('arguments').named_children
   if name.startswith('static_cast<'):return self.expr(args[0],e)
   if name=='ReadObjectKey':
    shape,key=self.expr(args[0],e),self.expr(args[1],e)
    if getattr(shape,'kind',shape)=='bad':self.assign(args[2].named_children[-1] if args[2].type=='pointer_expression' else args[2],e,0xc0000005);return False
    key.present=shape is not None;key.type=getattr(shape,'kind',shape);return True
   if name=='ProjectileAll':
    values=[self.expr(a,e) for a in args];characters,terrain=values[5:7];row=e['rows'][characters.index]
    calls=1 if row['wall']==0 or row.get('fallbackRayFail') else 2
    self.assign(args[-1],e,calls);e['scene'].commands.extend(['fallback']*calls)
    terrain.count=int(row['wall'] is not None);terrain.items=[NS(fraction=row['wall'])] if terrain.count else []
    characters.count=0 if calls==1 else row['hits'];characters.items=list(range(characters.count));characters.diagnostic=diag()
    return 3 if row.get('fallbackRayFail') else 0
  return super().expr(n,e)
 def assign(self,n,e,v):
  if n.type=='identifier' and self.txt(n)=='audit' and 'audit' in e:
   vars(e['audit']).update(vars(v));return
  return super().assign(n,e,v)
 def statement(self,n,e):
  if n.type=='else_clause':
   for child in n.named_children:self.statement(child,e)
   return
  if n.type=='break_statement':raise Break()
  if n.type=='continue_statement':raise Continue()
  if n.type in ('for_statement','while_statement'):
   ini=n.child_by_field_name('initializer');cond=n.child_by_field_name('condition');upd=n.child_by_field_name('update')
   if ini:self.statement(ini,e)
   loops=0
   while cond is None or self.expr(cond,e):
    try:self.statement(n.child_by_field_name('body'),e)
    except Break:break
    except Continue:pass
    if upd:self.expr(upd,e)
    loops+=1;assert loops<20000
   return
  if n.type=='declaration':
   typ=self.txt(n.child_by_field_name('type'))
   if typ=='IrisDiagnostics::Scope':return
   for item in n.named_children:
    if item.type in ('primitive_type','type_identifier','qualified_identifier','type_qualifier'):continue
    d=item.child_by_field_name('declarator') if item.type=='init_declarator' else item
    name=re.findall(r'\b\w+\b',self.txt(d))[0];v=item.child_by_field_name('value') if item.type=='init_declarator' else None
    if v and v.type=='argument_list':value=e[typ](*[self.expr(a,e) for a in v.named_children])
    elif v and typ in ('Diagnostic','RangedAudit') and v.type=='initializer_list':value=e[typ]()
    elif v:value=self.expr(v,e)
    elif d.type=='function_declarator':value=e[typ](*[e[self.txt(q)] for q in d.child_by_field_name('parameters').named_children])
    elif '[' in self.txt(d):value=[e[typ](i) if typ=='RangedSlot' else e[typ]() if typ=='RangedSpatialGroup' else None for i in range(8 if typ in ('RangedSlot','RangedSpatialGroup') else 64)]
    else:value=e[typ]() if typ in e and callable(e[typ]) else 0
    e[name]=copy.deepcopy(value) if isinstance(value,Box) and d.type!='reference_declarator' else value
   return
  return super().statement(n,e)
 def run_body(self,b,e):
  try:self.statement(b,e)
  except Returned as r:return r.value

def body_tokens(s):
 p=Program('void X()'+s);return p.tokens(p.body('X'))
def preserve_consumers(old,new):
 for name in ('ResolveJobs','PrepareShotBatch'):
  assert old.tokens(old.body(name))==new.tokens(new.body(name)),name
 s=new.txt(new.body('AdvanceEffects'))
 s=s.replace('const bool shotAudit=projectileWorkLogging&&IrisDiagnostics::DetailsEnabled();','').replace('const size_t initialShots=shots.size();size_t visitedShots=0;','')
 s=s.replace('for(size_t i=0;i<shots.size();++i){Shot& s=shots[i];s.pending+=dt*s.rate;\n        if(shotAudit){++s.auditUpdates;s.auditAge+=dt;s.auditMaxPending=std::max(s.auditMaxPending,s.pending);}}','for(size_t i=0;i<shots.size();++i)shots[i].pending+=dt*shots[i].rate;')
 s=s.replace('++visitedShots;','').replace('bool complete;unsigned issued=0;','bool complete;')
 s=s.replace('if(shotAudit)issued=shotBatchWork.results[next].rayCalls+shotBatchWork.results[next].bodyCalls;','')
 s=s.replace('if(shotAudit)++s.auditBudget;','').replace('const unsigned before=budget;','').replace('issued=before-budget;','')
 s=s.replace('if(shotAudit){++s.auditAttempts;s.auditCommands+=issued;\n            if(!complete){++s.auditWaits;if(!issued)++s.auditNoCommands;}\n            else if(!hits.count&&!terrain.count)++s.auditEmpty;}','')
 s=s.replace('LogShotWork(s,"range_limit",s.range);','').replace('LogShotWork(s,"impact",s.travel+step*f);','').replace('if(shotAudit)++s.auditBlast;','')
 s=s.replace('if(initialShots>visitedShots&&IrisDiagnostics::CollisionProfileEnabled())IrisDiagnostics::Add(IrisDiagnostics::PROJECTILE_UNVISITED,initialShots-visitedShots);','')
 assert body_tokens(s)==old.tokens(old.body('AdvanceEffects')),'AdvanceEffects'
 s=new.txt(new.body('Emit'))
 s=s.replace('const size_t oldCapacity=shots.capacity();\n    try{DrawShot(s,a.origin);shots.push_back(s);}catch(...){s.visual.Clear(true);throw;}\n    if(IrisDiagnostics::CollisionProfileEnabled()){\n        IrisDiagnostics::Add(IrisDiagnostics::PROJECTILE_SPAWNS);if(shots.capacity()!=oldCapacity)IrisDiagnostics::Add(IrisDiagnostics::PROJECTILE_VECTOR_GROWTH);\n    }','DrawShot(s,a.origin);shots.push_back(s);')
 oldemit=old.txt(old.body('Emit')).replace('if(shots.size()>=64)return false;','')
 assert body_tokens(s)==body_tokens(oldemit),'Emit'
 s=new.txt(new.body('WarmNext')).replace('Return(v);','pool.push_back(v);')
 assert body_tokens(s)==old.tokens(old.body('WarmNext')),'WarmNext'
 return ['AdvanceEffects minus audit only','Emit minus count gate and exception cleanup','WarmNext idle return','PrepareShotBatch','ResolveJobs']

def spatial_cases(vm,bodies,env,batch,fix,path,rng):
 def run(name,**kw):return vm.run_body(bodies[name],dict(env,**kw))
 def make(xs):return [dict(p=fix(path(x)),ray=0,body=0,hits=0,wall=None) for x in xs]
 def policy(budget=64,shadow=False,single=True,reuse=False):return NS(reuse=reuse,empty=True,shadow=shadow,allowEmpty=True,maxCalls=budget,spatial=True,single=single)
 count=0
 # 稠密空组减少实际SDK命令；保留最坏headroom，预算紧时不做额外试探。
 rows=make([0,.1,.2,.3])
 for budget in [8,9,64]:
  ok,res,a,c,p=batch(rows,budget,[],policy(budget));assert ok
  assert (a.savedSweeps,c)==((0,8) if budget==8 else (4,5));count+=1
 # 分散单条省扫掠但不省命令；不能把AABB代价隐去。
 rows=make([0,100,200,300])
 for single in [False,True]:
  ok,res,a,c,p=batch(rows,64,[],policy(single=single));assert c==8
  assert a.savedSweeps==(4 if single else 0);count+=1
 # 首组有角色，不阻止后两个空组。模拟宽相输入按box选择，精确输出另给定，不伪装执行SDK。
 rows=make([0,.1,100,100.1,200,200.1]);rows[0]['hits']=rows[1]['hits']=1
 box=Box();box.min=Vec(-1,-1,-1);box.max=Vec(1,1,1)
 ok,res,a,c,p=batch(rows,64,[NS(kind=11,box=box)],policy())
 assert (a.probeBusy,a.spatialGroups,a.savedSweeps,c,p.allowEmpty)==(1,3,4,11,True);count+=1
 # 阴影开启保留所有原扫掠；额外探针也算硬预算，不用未发生的省查抵扣。
 for budget in range(12,21):
  ok,res,a,c,p=batch(rows,budget,[NS(kind=11,box=box)],policy(budget,True))
  assert all(r.characters.count==rows[i]['hits'] for i,r in enumerate(res));assert not a.savedSweeps
  assert c==12+min(3,budget-12);count+=1
 # 故意让宽相空、精确非空，验证只记差异/禁后续省查，依旧消费精确名单。
 rows=make([0,.1,100,100.1]);rows[2]['hits']=1
 ok,res,a,c,p=batch(rows,64,[],policy(shadow=True))
 assert a.shadowMismatches==1 and not p.allowEmpty and res[2].characters.count==1;count+=1
 # 未知身份使未证明路径走原扫掠；早前已确认空组可用，不能吞掉后面的真实命中。
 rows=make([0,.1,100,100.1])
 bad=NS(kind='bad',box=box)
 # ReadObjectKey 的异常替身使用字符串bad；全局bad覆盖所有组，首组立即保守退出。
 ok,res,a,c,p=batch(rows,64,['bad'],policy())
 assert a.probeUnknown==1 and not p.allowEmpty and a.savedSweeps==0 and c==9;count+=1
 # 完整报告计数不符不能省查；首组空、第二组异常时，只保留首组已证明空区。
 class Broad(list):pass
 b=Broad();b.extraCount=1
 ok,res,a,c,p=batch(rows,64,b,policy())
 assert a.probeUnknown==1 and a.savedSweeps==0 and not p.allowEmpty;count+=1
 rows=make([0,.1,100,100.1,200,200.1])
 badbox=Box();badbox.min=Vec(99,-1,-1);badbox.max=Vec(101,1,1)
 rows[4]['hits']=1
 ok,res,a,c,p=batch(rows,64,[NS(kind='bad',box=badbox)],policy())
 assert a.savedSweeps==2 and a.probeUnknown==1 and not p.allowEmpty and res[4].characters.count==1;count+=1
 rows=make([0,.1,100,100.1])
 # 流式回调>64、>512均无候选上限。
 for n in [65,513,4097]:
  ok,res,a,c,p=batch(rows,64,[7]*n,policy());assert a.savedSweeps==4 and a.probeCandidates==2*n;count+=1
 # 完整实际RangedBatch：预算、失败重试、完全相同别名、墙及稀疏位置。
 for n,budget,mode,single,shadow in itertools.product(range(2,9),[4,8,12,16,17,32,64],['dense','sparse','mixed','wall','rayfail','bodyfail','aliasfail'],[False,True],[False,True]):
  rows=make([i*(100 if mode=='sparse' else .1) for i in range(n)])
  broad=[]
  if mode=='mixed':
   broad=[NS(kind=11,box=box)]
   for r in rows:r['hits']=1
  if mode=='wall':rows[0]['wall']=0.
  if mode=='rayfail':rows[0]['ray']=3
  if mode=='bodyfail':rows[0]['body']=3
  if mode=='aliasfail':
   rows[1]['p']=copy.deepcopy(rows[0]['p']);rows[0]['ray']=3
  p=policy(budget,shadow,single,mode=='aliasfail');ok,res,a,c,p=batch(rows,budget,broad,p)
  assert ok==(budget>=2*n)
  if ok and mode=='aliasfail':assert a.reuseFailed==1 and res[1].source==1 and res[1].status==0
  count+=1
 # 实际聚组AST：掩码不丢不重、包络不缩小、输入顺序不改、含无效元素时只剔除该元素。
 geometries=0
 for trial in range(480):
  n=rng.randrange(1,9);paths=[fix(path(rng.choice([0,1,10,100,1000])+rng.random(),10**rng.uniform(-3,2),rng.uniform(-20,20))) for i in range(n)]
  if trial%13==0:paths[-1].radius=float('inf')
  mask=rng.randrange(1<<n);clusters=[env['RangedSpatialGroup']() for _ in range(8)];a=NS(**dict.fromkeys(FIELDS,0));snapshot=copy.deepcopy(paths)
  run('BuildRangedSpatialGroups',paths=paths,count=n,mask=mask,groups=clusters,audit=a)
  expected=0
  for i,p in enumerate(paths):
   b=Box()
   if mask&(1<<i) and run('RangedSweepBounds',p=p,box=b):expected|=1<<i
  found=0
  for g in clusters[:n]:
   if not g.mask:continue
   assert not found&g.mask;found|=g.mask;assert g.paths==g.mask.bit_count()
   for i,p in enumerate(paths):
    if g.mask&(1<<i):
     b=Box();assert run('RangedSweepBounds',p=p,box=b)
     assert all(g.bounds.min[d]<=b.min[d] and g.bounds.max[d]>=b.max[d] for d in range(3))
  assert found==expected
  for i,p in enumerate(paths):
   assert struct.pack('<f',p.radius)==struct.pack('<f',snapshot[i].radius)
  # 重跑必须相同，不靠随机或可变SDK状态分组。
  again=[env['RangedSpatialGroup']() for _ in range(8)];a2=NS(**dict.fromkeys(FIELDS,0))
  run('BuildRangedSpatialGroups',paths=paths,count=n,mask=mask,groups=again,audit=a2)
  assert [g.mask for g in clusters]==[g.mask for g in again];geometries+=1
 return dict(actual_batches=count,partition_envelope_trials=geometries,partial_busy_group_does_not_disable_other_empty_groups=True,singletons_same_command_count=True,budget_includes_extra_probes=True)

class Pool:
 def __init__(self,items=()):self.items=list(items)
 def size(self):return len(self.items)
 def begin(self):return 0
 def erase(self,i):self.items.pop(i)
 def push_back(self,v):self.items.append(copy.copy(v))
class Visual:
 nextid=1
 def __init__(self):self.entity=0;self.key='';self.hidden=False;self.releases=[]
 def Create(self,key):self.key=key;self.entity=Visual.nextid;Visual.nextid+=1
 def Hide(self):self.hidden=True
 def Clear(self,destroy):assert destroy;self.releases.append(self.entity);self.entity=0
class LifeVM(VM):
 def expr(self,n,e):
  if n.type=='subscript_expression' and self.txt(n.child_by_field_name('argument'))=='pool':return e['pool'].items[self.expr(n.child_by_field_name('indices').named_children[0],e)]
  return super().expr(n,e)
 def assign(self,n,e,v):
  if n.type=='identifier' and self.txt(n)=='v' and 'v' in e:
   vars(e['v']).update(vars(v));return
  return super().assign(n,e,v)
 def statement(self,n,e):
  if n.type=='try_statement':
   body=next(c for c in n.named_children if c.type=='compound_statement')
   try:self.statement(body,e)
   except MemoryError:
    handler=next(c for c in n.named_children if c.type=='catch_clause')
    self.statement(handler.child_by_field_name('body'),e)
   return
  if n.type=='throw_statement':raise MemoryError('mock rethrow')
  return super().statement(n,e)
def lifecycle(combat):
 vm=LifeVM(combat.source.decode());counts=0
 for active in [0,63,64,65,95,96,128,512,4096]:
  for idle in [0,95,96,128]:
   pool=Pool();pool.items=[NS(key='other') for i in range(idle)];v=Visual();events=[]
   e=dict(v=v,key='bullet',pool=pool,shots=NS(size=lambda:active),residues=NS(size=lambda:active),Visual=Visual)
   e['IrisDiagnostics::Add']=lambda *args:events.append(args);e['IrisDiagnostics::POOL_REUSES']=0
   assert vm.run_body(definitions(vm,'Borrow'),e);assert v.entity and v.key=='bullet';counts+=1
 # 归还最多96个闲置，每个额外实例清一次；活动Visual不在池中。
 pool=Pool();e=dict(pool=pool,Visual=Visual);e['IrisDiagnostics::CollisionProfileEnabled']=lambda:True;e['IrisDiagnostics::Add']=lambda *args:None;e['IrisDiagnostics::IDLE_POOL_TRIMS']=0
 for i in range(512):
  v=Visual();v.Create('bullet');entity=v.entity;e['v']=v;vm.run_body(definitions(vm,'Return'),e)
  assert not v.entity and pool.size()==min(i+1,96)
  if i>=96:assert v.releases==[entity]
  counts+=1
 v=Visual();e.update(v=v,key='bullet');e['IrisDiagnostics::POOL_REUSES']=0
 assert vm.run_body(definitions(vm,'Borrow'),e) and v.entity and pool.size()==95;counts+=1
 # 直接解释实际Emit插入段：正常接收>旧64/96/512上限，Draw/push失败释放临时所有者并抛回原异常边界。
 body=definitions(vm,'Emit');src=vm.txt(body);segment=src[src.index('const size_t oldCapacity=shots.capacity();'):src.index('if(IrisDiagnostics::DetailsEnabled()){std::ostringstream out;out<<"projectile_spawn')]
 emit=LifeVM('void Insert(){'+segment+'}');ib=definitions(emit,'Insert')
 class Shots:
  def __init__(self,n,fail):self.n=n;self.fail=fail;self.s=None
  def capacity(self):return self.n
  def push_back(self,s):
   if self.fail:raise MemoryError('push')
   self.n+=1;self.s=s
 for n,fail in itertools.product([0,64,96,512,4096],['none','draw','push']):
  v=Visual();v.Create('bullet');entity=v.entity;s=NS(visual=v);shots=Shots(n,fail=='push')
  def draw(*args):
   if fail=='draw':raise MemoryError('draw')
  env=dict(s=s,a=NS(origin=0),shots=shots,DrawShot=draw)
  env.update({'IrisDiagnostics::CollisionProfileEnabled':lambda:False})
  try:emit.run_body(ib,env)
  except MemoryError:assert fail!='none' and v.releases==[entity] and shots.n==n
  else:assert fail=='none' and shots.n==n+1 and v.entity==entity and not v.releases
  counts+=1
 # 关闭逐弹诊断必须首门返回，不能格式化、读时钟或访问Shot。
 lb=definitions(vm,'LogShotWork')
 for own,parent in [(False,False),(False,True),(True,False)]:
  vm.run_body(lb,dict(projectileWorkLogging=own,**{'IrisDiagnostics::DetailsEnabled':lambda:parent}));counts+=1
 return dict(actual_AST_lifecycle_cases=counts,active_capacity_tests_up_to=4096,idle_pool_retains_at_most=96,draw_and_vector_failure_cleanup=True,disabled_shot_logging_short_circuits=True)

def main(before,out):
 native=VM(norm(txt(ROOT/'native/NativeMultiContact.cpp')));combat=Program(txt(ROOT/'IrisCombat.cpp'))
 oldn=Program(norm(txt(before/'native/NativeMultiContact.cpp')));oldc=Program(txt(before/'IrisCombat.cpp'))
 protected=0
 for old,new,skip in [(oldn,native,{'RangedBatch'}),(oldc,combat,{'Configure','RunRangedBatch','AdvanceEffects','Emit','Borrow','Return','WarmNext'})]:
  for node in old.nodes('function_definition'):
   b=node.child_by_field_name('body');header=old.source[node.start_byte:b.start_byte].decode()
   if any(re.search(r'\b'+x+r'\s*\(',header) for x in skip):continue
   match=[n.child_by_field_name('body') for n in new.nodes('function_definition') if re.sub(r'audit\w+\(0\),','',new.source[n.start_byte:n.child_by_field_name('body').start_byte].decode())==header]
   assert match,(header,len(match));assert any(old.tokens(b)==new.tokens(q) for q in match),header;protected+=1
 # 实际消费/医疗/调度既有函数逐token原样；纯观察插入点另做整函数恢复比对。
 consumer_preserved=preserve_consumers(oldc,combat)
 # 解释实际函数，外部调用替身只提供SDK值，不重写产品分支。
 bodies={x:definitions(native,x) for x in ('SameRangedFloat','SameRangedInput','RangedSweepBounds','RangedBoundsVolume','ProbeRangedEmpty','BuildRangedSpatialGroups','ProbeRangedSpatial','RangedBatch')}
 cb=next(n for n in native.nodes('class_specifier') if native.txt(n.child_by_field_name('name'))=='RangedEmptyReport')
 callback=next(n.child_by_field_name('body') for n in native.nodes('function_definition') if cb.start_byte<n.start_byte<n.end_byte<cb.end_byte and 'onEvent(' in native.source[n.start_byte:n.child_by_field_name('body').start_byte].decode())
 env={'unsigned':int,'double':float,'float':f32,'std::min':min,'std::max':max,'fabs':abs,'_finite':math.isfinite,'Finite':math.isfinite,'FLT_EPSILON':2**-23,'FLT_MAX':f32(3.4028234663852886e38),'CHARACTER':11,'NxBounds3':Box,'NxVec3':Vec,'ObjectKey':lambda:NS(present=False,type=0),'NX_ALL_SHAPES':3,'IrisDiagnostics::RANGED_EMPTY_PROBE':0,'IrisDiagnostics::RANGED_SPATIAL_BUILD':0}
 env['std::memcmp']=lambda a,b,n:0 if struct.pack('<f',a)==struct.pack('<f',b) else 1
 def call(name,**kw):return native.run_body(bodies[name],dict(env,**kw))
 env['SameRangedFloat']=lambda a,b:call('SameRangedFloat',a=a,b=b)
 env['SameRangedInput']=lambda a,b:call('SameRangedInput',a=a,b=b)
 env['RangedSweepBounds']=lambda p,box:call('RangedSweepBounds',p=p,box=box)
 env['RangedBoundsVolume']=lambda box:call('RangedBoundsVolume',box=box)
 env['RangedSpatialGroup']=lambda:NS(bounds=Box(),mask=0,paths=0)
 env['BuildRangedSpatialGroups']=lambda paths,count,mask,groups,audit:call('BuildRangedSpatialGroups',paths=paths,count=count,mask=mask,groups=groups,audit=audit)
 def report():
  r=NS(candidates=0,characters=0,unknown=0,exception=0)
  def event(n,shapes):
   e=dict(env,**vars(r),count=n,shapes=shapes);ret=native.run_body(callback,e)
   for k in ('candidates','characters','unknown','exception'):setattr(r,k,e[k])
   return ret
  r.onEvent=event;return r
 env['RangedEmptyReport']=report
 def path(x=0,r=4.5,m=5):return NS(from_=NS(x=f32(x),y=0.,z=0.),motion=NS(x=f32(m),y=0.,z=0.),radius=f32(r),cylinder=False)
 def fix(p):setattr(p,'from',p.from_);return p
 p=fix(path());keycases=0
 for axis in range(8):
  q=copy.deepcopy(p)
  if axis<3:setattr(getattr(q,'from'),['x','y','z'][axis],f32(1e-20))
  elif axis<6:setattr(q.motion,['x','y','z'][axis-3],f32(getattr(q.motion,['x','y','z'][axis-3])+1e-5))
  elif axis==6:q.radius=f32(p.radius+1e-5)
  else:q.cylinder=True
  assert not call('SameRangedInput',a=p,b=q);keycases+=1
 q=copy.deepcopy(p);q.from_.x=-0.;assert not call('SameRangedInput',a=p,b=q);assert call('SameRangedInput',a=p,b=p)
 rng=random.Random(890040);bounds=0
 for _ in range(1500):
  p=fix(path(rng.uniform(-1e8,1e8),10**rng.uniform(-3,4),rng.uniform(-1e6,1e6)))
  p.from_.y=f32(rng.uniform(-1e8,1e8));p.from_.z=f32(rng.uniform(-1e8,1e8))
  p.motion.y=f32(rng.uniform(-1e6,1e6));p.motion.z=f32(rng.uniform(-1e6,1e6));box=Box()
  assert call('RangedSweepBounds',p=p,box=box)
  for t in [0.,1.,f32(1.001),rng.uniform(0,1.001)]:
   for a in range(3):
    v=[p.from_.x,p.from_.y,p.from_.z][a]+[p.motion.x,p.motion.y,p.motion.z][a]*t
    assert box.min[a]<=v-p.radius and box.max[a]>=v+p.radius
   bounds+=1
 # 回调流式无固定候选上限；未知身份阻止省查，角色返回后不继续读取后续坏指针。
 callbacks=0
 for n in [0,1,63,64,65,512,513,4097]:
  r=report()
  for a in range(0,n,64):assert r.onEvent(min(64,n-a),[7]*min(64,n-a))
  assert r.candidates==n and not r.characters and not r.unknown;callbacks+=1
 for data in [[11,'bad'],['bad',11],[None,11],[None,None]]:
  r=report();r.onEvent(len(data),data);assert bool(r.characters or r.unknown)==(11 in data or 'bad' in data or None in data);callbacks+=1
 class Scene:
  def __init__(self,rows,broad):self.rows=rows;self.broad=broad;self.commands=[];self.queue=[];self.sdk=object()
  def getPhysicsSDK(self):return self.sdk
  def overlapAABBShapes(self,box,kind,n,chunk,r,*args):
   self.commands.append('probe')
   selected=[s for s in self.broad if not hasattr(s,'box') or all(box.min[a]<=s.box.max[a] and s.box.min[a]<=box.max[a] for a in range(3))]
   for i in range(0,len(selected),n):
    data=selected[i:i+n]
    if not r.onEvent(len(data),data):break
   return len(selected)+getattr(self.broad,'extraCount',0)
  def createSceneQuery(self,d):return self
  def raycastAllShapes(self,*args):self.queue.append(('ray',args[-1]));self.commands.append('ray')
  def linearCapsuleSweep(self,*args):self.queue.append(('body',args[-1]));self.commands.append('body')
  def Finish(self):
   for kind,s in self.queue:
    row=self.rows[s.index]
    if kind=='ray':
     s.ray.status=row['ray'];s.ray.out.count=int(row['wall'] is not None);s.ray.out.items=[NS(fraction=row['wall'])] if s.ray.out.count else []
    else:s.sweep.status=row['body'];s.sweep.out.count=row['hits'];s.sweep.out.items=list(range(row['hits']))
   self.queue.clear()
 def slot(i):return NS(index=i,travel=Vec(),axis=Vec(),capsule=NS(p0=Vec(),p1=Vec(),radius=0),rayStorage=None,sweepStorage=None,ray=None,sweep=None)
 cases=0;saved=0
 def batch(rows,budget,broad,policy):
  if not hasattr(policy,'spatial'):policy.spatial=False
  if not hasattr(policy,'single'):policy.single=False
  scene=Scene(rows,broad);results=[NS(characters=contacts(i),terrain=contacts(i)) for i in range(len(rows))]
  audit=NS(**dict.fromkeys(FIELDS,0));owner=NS(scene=scene,query=None,pending=False,Finish=scene.Finish)
  e=dict(env,world=scene,scene=scene,rows=rows,paths=[r['p'] for r in rows],count=len(rows),groups=0xffffffff,results=results,queryCalls=0,policy=policy,audit=audit,
   Initialize=lambda:True,getSdk=lambda:scene.sdk,RANGED_BATCH_CAPACITY=8,RangedAudit=lambda:NS(**dict.fromkeys(FIELDS,0)),RangedSlot=slot,RangedReport=lambda s,n:NS(bad=False),RangedQueryOwner=lambda s:owner,NxSceneQueryDesc=lambda:NS(report=None,executeMode=0),Diagnostic=diag,NxRay=lambda a,b:NS(origin=a,dir=b),TerrainRayCollector=lambda out,*args:NS(out=out,status=0),Collector=lambda out,*args:NS(out=out,status=0),NxSphere=lambda:NS(center=Vec(),radius=0),NX_SQE_SYNCHRONOUS=0,NX_RAYCAST_SHAPE=1,NX_RAYCAST_DISTANCE=2,NATIVE_BOLT_GROUPS=0x087fde47,NX_SF_STATICS=1,NX_SF_DYNAMICS=2,NX_SF_ALL_HITS=4,ISSUE_NONE=0,ISSUE_BATCH_INPUT=1,QUERY_COMPLETE=0,QUERY_INVALID=3,FinalizeSweep=lambda out,status:status)
  for name in ['DetailsEnabled','CollisionProfileEnabled']:e['IrisDiagnostics::'+name]=lambda:False
  for name in ['RANGED_REUSE_LOOKUP','RANGED_BATCH_CREATE','RANGED_BATCH_RAYS','RANGED_BATCH_BODIES']:e['IrisDiagnostics::'+name]=0
  def probe(*args):
   local=dict(e,scene=args[0],paths=args[1],count=args[2],mask=args[3],groups=args[4],calls=e['queryCalls'],policy=args[6],audit=args[7])
   ret=native.run_body(bodies['ProbeRangedSpatial' if local['policy'].spatial else 'ProbeRangedEmpty'],local);e['queryCalls']=local['calls'];return ret
  e['ProbeRangedEmpty']=e['ProbeRangedSpatial']=probe
  ok=native.run_body(bodies['RangedBatch'],e)
  assert e['queryCalls']==len(scene.commands) and e['queryCalls']<=budget
  if ok:
   for i,r in enumerate(results):
    assert 0<=r.source<=i;v=results[r.source];assert r.source==i or v.status==0
    if v.status==0:assert v.characters.count==(0 if rows[i]['wall']==0 else rows[i]['hits'])
  return ok,results,audit,e['queryCalls'],policy
 for count,mode,shadow,reuse,budgetExtra in itertools.product(range(2,9),['empty','busy','sparse','duplicate','duplicate_hits','bad','wall','rayfail','bodyfail'],[False,True],[False,True],[0,1,20]):
  rows=[]
  for i in range(count):
   x=0 if mode.startswith('duplicate') else i*(1000 if mode=='sparse' else .25)
   rows.append(dict(p=fix(path(x)),ray=3 if mode=='rayfail' and i==0 else 0,body=3 if mode=='bodyfail' and i==0 else 0,hits=1 if mode in ('busy','duplicate_hits') else 0,wall=0 if mode=='wall' else None))
  broad=[11] if mode in ('busy','duplicate_hits') else ['bad'] if mode=='bad' else []
  policy=NS(reuse=reuse,empty=True,shadow=shadow,allowEmpty=True,maxCalls=min(64,count*2+budgetExtra))
  ok,res,a,c,pol=batch(rows,policy.maxCalls,broad,policy);assert ok
  if not shadow:saved+=a.savedSweeps
  assert a.shadowMismatches==int(shadow and mode=='bodyfail' and a.emptyPaths>0)
  if a.probeBusy:assert not pol.allowEmpty and a.savedSweeps==0
  if mode.startswith('duplicate') and reuse:assert a.reused==count-1 and c==2
  if mode=='duplicate_hits':assert sum(res[r.source].characters.count for r in res)==count
  cases+=1
 # 关闭优化、下次更新恢复、输入拒绝和逐次预算，均走实际产品AST。
 extra=0
 for n,budget,enabled,allow in itertools.product(range(2,9),[0,1,3,4,8,16,17,31,32,33,63,64],[False,True],[False,True]):
  rows=[dict(p=fix(path(.25*i)),ray=0,body=0,hits=0,wall=None) for i in range(n)]
  policy=NS(reuse=False,empty=enabled,shadow=False,allowEmpty=allow,maxCalls=budget)
  ok,res,a,c,pol=batch(rows,budget,[],policy);assert ok==(budget>=2*n)
  if not enabled or not allow:assert a.probeCalls==0 and a.savedSweeps==0
  extra+=1
 for value,field in itertools.product([0.,-1.,float('nan'),float('inf')],['radius','origin','motion']):
  rows=[dict(p=fix(path(.25*i)),ray=0,body=0,hits=0,wall=None) for i in range(4)]
  if field=='radius':rows[2]['p'].radius=value
  elif field=='origin':rows[2]['p'].from_.x=value
  else:rows[2]['p'].motion=NS(x=value,y=0.,z=0.)
  if field!='radius' and math.isfinite(value) and value!=0:continue
  if field=='origin' and value==0:continue
  if field=='motion' and value==0:pass
  ok,res,a,c,pol=batch(rows,64,[],NS(reuse=True,empty=True,shadow=False,allowEmpty=True,maxCalls=64))
  assert not ok and c==0;extra+=1
 # 同批不合并事件：实际RangedValue借用同一事实，八个事件仍分别消费一条命中。
 valueVM=VM(txt(ROOT/'IrisCombat.cpp'));valueBody=definitions(valueVM,'RangedValue')
 rows=[dict(p=fix(path()),ray=0,body=0,hits=1,wall=None) for i in range(8)]
 ok,res,a,c,pol=batch(rows,64,[11],NS(reuse=True,empty=True,shadow=False,allowEmpty=True,maxCalls=64))
 consumed=[]
 for i in range(8):
  fact=valueVM.run_body(valueBody,dict(work=NS(results=res),index=i))
  assert fact is res[res[i].source];consumed.append((100+i,200+i,fact.characters.count))
 assert len(set((cast,event) for cast,event,hits in consumed))==8 and sum(h for _,_,h in consumed)==8 and c==2
 extra+=1
 # 已知失败不缓存，别名实际独立执行；测试反例必须保留原扫掠并记录不一致。
 rows=[dict(p=fix(path(0 if i<2 else .25*i)),ray=3 if i==0 else 0,body=0,hits=0,wall=None) for i in range(4)]
 ok,res,a,c,_=batch(rows,64,[],NS(reuse=True,empty=True,shadow=False,allowEmpty=True,maxCalls=64))
 assert a.reuseFailed==1 and res[1].source==1 and res[1].status==0
 # 原来失败不会被“复用成功”吞掉；shadow发现不一致仍消费SDK结果。
 rows=[dict(p=fix(path(.25*i)),ray=0,body=0,hits=1,wall=None) for i in range(4)]
 ok,res,a,c,pol=batch(rows,64,[],NS(reuse=False,empty=True,shadow=True,allowEmpty=True,maxCalls=64))
 assert a.shadowMismatches==4 and not pol.allowEmpty and all(r.characters.count==1 for r in res)
 spatial_result=spatial_cases(native,bodies,env,batch,fix,path,rng)
 lifecycle_result=lifecycle(combat)
 syntax=[]
 for f in list(ROOT.glob('*.cpp'))+list(ROOT.glob('*.h'))+list((ROOT/'native').glob('*.cpp'))+list((ROOT/'native').glob('*.h')):
  s=norm(txt(f));s=re.sub(r'typedef Item\*\(RootObjectFactory::\* CreateMember\)\([^;]+;','typedef void* CreateMember;',s);Program(s);syntax.append(str(f.relative_to(ROOT)))
 diagtext=txt(ROOT/'IrisDiagnostics.cpp');header=txt(ROOT/'IrisDiagnostics.h')
 for enum,array in [('Kind','names'),('Counter','counters')]:
  enums=re.search('enum '+enum+r' \{([^}]+)\}',header)[1].split(',')[:-1];names=re.findall(r'"[^"]+"',re.search(array+r'\[[A-Z_]+\]=\{([^}]+)\}',diagtext)[1]);assert len(enums)==len(names)
 # 实际日志门与Scope时钟位置：任一父门关闭，新通道不读Now、不累计计数锁。
 dvm=VM(norm(diagtext));activeBody=free_body(dvm,'Active');collisionBody=free_body(dvm,'CollisionProfileEnabled');detailsBody=free_body(dvm,'DetailsEnabled')
 gateCases=0
 kindNames=[x.strip() for x in re.search(r'enum Kind \{([^}]+)\}',header)[1].split(',')[:-1]]
 for enabled,performance,details,collision in itertools.product([False,True],repeat=4):
  e=dict(enabled=enabled,performance=performance,details=details,collisionProfile=collision,NATIVE_TERRAIN_RAY=kindNames.index('NATIVE_TERRAIN_RAY'))
  e['DetailsEnabled']=lambda e=e:dvm.run_body(detailsBody,e)
  e['CollisionProfileEnabled']=lambda e=e:dvm.run_body(collisionBody,e)
  for kind in ('RANGED_REUSE_LOOKUP','RANGED_EMPTY_PROBE','RANGED_SPATIAL_BUILD'):
   assert dvm.run_body(activeBody,dict(e,k=kindNames.index(kind)))==all([enabled,performance,details,collision]);gateCases+=1
 ctor=definitions(dvm,'Scope');assert 'if(active)' in dvm.txt(ctor) and 'begin=Now()' in dvm.txt(ctor)
 for f in ('distribution/IrisArsenal.ini','package/IrisArsenal/IrisArsenal.ini'):
  c=configparser.ConfigParser();c.read(ROOT/f,encoding='utf8');assert c['IrisArsenal']['EnableRangedQueryReuse']=='1' and c['IrisArsenal']['EnableRangedEmptyPruning']=='1' and c['IrisArsenal']['EnableRangedEmptyShadow']=='0'
 for f in ('tools/stage_package.py','tools/test_update_mod.py',__file__):ast.parse(txt(Path(f) if str(f)==__file__ else ROOT/f))
 result=dict(actual_CPP_AST_batches=cases+extra+2,exact_key_fields_and_signed_zero=keycases+2,swept_sphere_envelope_samples=bounds,streaming_callback_cases=callbacks,mock_empty_sweeps_saved=saved,spatial=spatial_result,lifecycle=lifecycle_result,protected_original_functions=protected,actual_logging_gate_cases=gateCases,full_consumers_preserved=consumer_preserved,syntax_units=syntax,medical_FIFO_specs=replay(txt(ROOT/'IrisCombat.cpp')),compiled=False,real_PhysX_or_threads_or_game_tested=False,FPS_measured=False)
 out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--before',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();main(a.before,a.out)
