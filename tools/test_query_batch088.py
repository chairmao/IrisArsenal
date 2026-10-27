"""088非编译验证：执行实际预取/预留AST、调度规格回放和原链逐token检查；不模拟PhysX实现。"""
from pathlib import Path
from types import SimpleNamespace as NS
import sys,re,json,random,copy,configparser,hashlib,ast,itertools,argparse
ROOT=Path(__file__).resolve().parents[1]
cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--before',type=Path,required=True);cli.add_argument('--out',type=Path,required=True);args=cli.parse_args();BEFORE=args.before;TASK=args.out.parent
sys.path.insert(0,str(ROOT/'tools'))
from test_native_profile084 import Eval,definitions
from test_performance080 import Program,Returned
from test_medical_gate083 import replay
def text(path):return path.read_text('utf-8-sig')
def norm(s):return re.sub(r'__declspec\((?:[^()]|\([^()]*\))*\)','',s)
cp=Program(text(ROOT/'IrisCombat.cpp'));old=Program(text(BEFORE/'IrisCombat.cpp'))
np=Program(norm(text(ROOT/'native/NativeMultiContact.cpp')));on=Program(text(BEFORE/'native/NativeMultiContact.cpp'))
def tok(p,name):return p.tokens(p.body(name))
changed=['TryCapsuleBatch','ResolveJobs','AdvanceEffects']
protected=0
for node in old.nodes('function_definition'):
 body=node.child_by_field_name('body');header=old.source[node.start_byte:body.start_byte].decode();name=re.findall(r'(\w+)\s*\(',header)[0]
 if name in changed or name=='PlannedJobCost':continue
 if name in ('Load','LoadParameters'):continue
 try:other=cp.body(name)
 except AssertionError:continue
 if old.tokens(body)!=cp.tokens(other):
  # 实际配置装载函数仅增加本轮开关及启动日志，不属于战斗消费者。
  assert 'EnableCapsuleBatching' in old.txt(body),name
 else:protected+=1
for name in ['ReadObjectKey','RayBlocker','ProjectileAll','OverlapSphere','OverlapCapsule','OverlapCapsules','CylinderAll','BodyGeometry']:
 assert tok(np,name)==tok(on,name),name
# 核心消费者完整片段保持：资格/TOI/墙优先/Blast/位置推进、医疗入口与FIFO保持。
oldshot=old.txt(old.body('AdvanceEffects'));newshot=cp.txt(cp.body('AdvanceEffects'))
start='        s.retries=0;';end='    for(size_t i=0;i<residues.size();'
def token_fragment(s):return Program('void check(){'+s+'}').tokens(Program('void check(){'+s+'}').body('check'))
a=oldshot[oldshot.index(start):oldshot.index(end)];b=newshot[newshot.index(start):newshot.index('    if(next<ready)',newshot.index(start))]
# 片段尾部包含外层while的右括号，包入额外while后语法完整。
assert token_fragment('while(true){'+a)==token_fragment('while(true){'+b)
assert tok(cp,'Flush')==tok(old,'Flush')
# 原SweepAll整理阶段抽取为共用函数，内容只把collector.status参数化。
s=on.txt(on.body('SweepAll'));s=s[s.index('    if(IrisDiagnostics::CollisionProfileEnabled())IrisDiagnostics::Add(IrisDiagnostics::SWEEP_RAW'):]
s=s.replace('collector.status','status');assert token_fragment(s[:-1])==tok(np,'FinalizeSweep')

class Break(Exception):pass
class Vec(list):
 def size(self):return len(self)
class It:
 def __init__(self,rows,index):self.rows,self.index=rows,index
 def __add__(self,n):return It(self.rows,self.index+n)
 def __eq__(self,other):return isinstance(other,It) and self.rows==other.rows and self.index==other.index
 def __getattr__(self,k):return getattr(self.rows[self.index],k)
class Jobs(Vec):
 def begin(self):return It(self,0)
 def end(self):return It(self,len(self))
class VM(Eval):
 def expr(self,n,e):
  if n.type=='update_expression':
   a=n.named_children[0];old=self.expr(a,e);v=old+(-1 if '--' in self.txt(n) else 1);self.assign(a,e,v)
   return old if n.children[-1].type in ('++','--') else v
  if n.type=='assignment_expression':
   l=n.child_by_field_name('left');r=n.child_by_field_name('right');op=self.source[l.end_byte:r.start_byte].decode().strip();v=self.expr(r,e)
   if op=='-=':v=self.expr(l,e)-v
   elif op=='+=':v=self.expr(l,e)+v
   else:assert op=='='
   self.assign(l,e,v);return v
  return super().expr(n,e)
 def statement(self,n,e):
  if n.type=='break_statement':raise Break()
  if n.type=='declaration' and self.txt(n).startswith('IrisNative::CapsuleInput input['):
   e['input']=[NS(from_=NS(x=0,y=0,z=0),to=NS(x=0,y=0,z=0),radius=0) for _ in range(8)]
   for i in e['input']:setattr(i,'from',i.from_)
   return
  if n.type in ('for_statement','while_statement'):
   init=n.child_by_field_name('initializer');cond=n.child_by_field_name('condition');upd=n.child_by_field_name('update')
   if init:self.statement(init,e)
   guard=0
   while cond is None or self.expr(cond,e):
    try:self.statement(n.child_by_field_name('body'),e)
    except Break:break
    if upd:self.expr(upd,e)
    guard+=1;assert guard<10000
   return
  return super().statement(n,e)
def execute(p,body,e):
 try:p.statement(body,e)
 except Returned as r:return r.value
def point(v=0):return NS(x=v,y=v+1,z=v+2)
def path(kind='v',v=0):return NS(volume=kind=='v',sphere=kind=='s',cylinder=kind=='c',radius=4.5,to=point(v+1),**{'from':point(v)})

# 真实TryCapsuleBatch头部和几何值拷贝AST；SDK调用以后的调度另作规格回放。
head=cp.txt(cp.body('TryCapsuleBatch')).split('    unsigned calls=0;')[0]+'return count;}'
vm=VM('unsigned check()'+head);cases=0
for budget,used,kinds,allow,enabled in itertools.product(range(65),range(9),['vvvvvvvvv','vsvvvvvv','v','cvvvvv','vvvsvvv'],[False,True],[False,True]):
 job=NS(cursor=0,paths=Vec(path(k,i) for i,k in enumerate(kinds)));e=dict(job=job,budget=budget,used=used,allowBatch=allow,capsuleBatchEnabled=enabled,failed=True,
   w=NS(physics=NS(queuesAreClearMT=lambda:True)),**{'std::min':min,'IrisDiagnostics::Add':lambda *a:None,'IrisDiagnostics::CollisionProfileEnabled':lambda:False,'IrisDiagnostics::BATCH_ELIGIBLE':1,'IrisDiagnostics::BATCH_LOCAL_BLOCKED':2,'IrisDiagnostics::BATCH_LOCAL_RESERVATION':3})
 n=execute(vm,vm.body('check'),e)
 eligible=allow and enabled and used<7 and kinds.startswith('vv') and budget>=3
 expected=min(len(kinds.split('s')[0]),8-used,budget-1) if eligible else False
 assert n==expected,(budget,used,kinds,n,expected)
 if n:
  assert n+1<=budget and n+used<=8
  for i in range(n):assert e['input'][i].radius==job.paths[i].radius and e['input'][i].to==job.paths[i].to
 cases+=1

# 实际PrepareShotBatch/PrepareBeamBatch：捕获提交参数与数量，不代替SDK执行。
vm=VM(text(ROOT/'IrisCombat.cpp'));shot_body=vm.body('PrepareShotBatch');beam_body=vm.body('PrepareBeamBatch');rng=random.Random(880039);prepare=0
def work():return NS(tags=[NS(cast=0,event=0,cursor=0) for _ in range(8)],inputs=[NS() for _ in range(8)])
for _ in range(1500):
 rows=Vec(NS(cast=i+1,event=i%4,move=rng.choice([0,5,6]),range=100,travel=rng.choice([0,90,100]),speed=2,pending=rng.choice([0,1,3]),pos=i,direction=1,collisionRadius=4.5) for i in range(rng.randrange(1,30)))
 visits=rng.randrange(1,len(rows)+1);budget=rng.randrange(65);cursor=rng.randrange(100);enabled=rng.choice([True,False]);ws=work();capt=[]
 def submit(w,work,count,b):capt.append(count);return count>=2
 def pcopy(p,c,out):out.start=p.a;out.end=p.b;out.radius=p.r;out.cylinder=c
 e={'shots':rows,'shotCursor':cursor,'visits':visits,'budget':budget,'rangedBatchEnabled':enabled,'w':object(),'shotBatchWork':ws,'std::min':min,'IrisNative::RANGED_BATCH_CAPACITY':8,'RangedMove':lambda m:m in (5,6),'Path':lambda a,b,r:NS(a=a,b=b,r=r),'RangedPath':pcopy,'RunRangedBatch':submit}
 got=execute(vm,shot_body,e);n=0
 if enabled and budget>=4 and visits>=2 and len(rows)>=2:
  for i in range(min(8,budget//2,visits,len(rows))):
   r=rows[(cursor%len(rows)+i)%len(rows)]
   if r.move==0 or min(r.range-r.travel,r.speed*r.pending)<=.000001:break
   n+=1
 assert got==(n if n>=2 else 0)
 for i in range(got):assert ws.tags[i].cast==rows[(cursor+i)%len(rows)].cast
 prepare+=1
for _ in range(1200):
 rows=Jobs(NS(cast=i+1,event=i%4,cursor=rng.randrange(2),paths=Vec()) for i in range(rng.randrange(1,25)))
 for r in rows:r.paths=Vec(path(rng.choice(['c','c','v']),i) for i in range(rng.randrange(1,4)))
 visits=rng.randrange(1,len(rows)+1);budget=rng.randrange(65);enabled=rng.choice([True,False]);ws=work()
 e={'jobs':rows,'visits':visits,'budget':budget,'rangedBatchEnabled':enabled,'w':object(),'beamBatchWork':ws,'std::min':min,'IrisNative::RANGED_BATCH_CAPACITY':8,'RangedPath':lambda p,c,out:setattr(out,'radius',p.radius),'RunRangedBatch':lambda w,work,n,b:n>=2}
 got=execute(vm,beam_body,e);n=0
 if enabled and budget>=4 and visits>=2:
  for r in rows[:min(8,budget//2,visits)]:
   if r.cursor+1!=len(r.paths) or not r.paths[r.cursor].cylinder:break
   n+=1
 assert got==(n if n>=2 else 0)
 prepare+=1

# 调度规格：各种删除/失败/零步长/零墙/奇数预算；SDK结果当作既定纯值输入。
def shots_run(data,cursor,budget,batch):
 shots=copy.deepcopy(data);visits=len(shots);trace=[];calls=0;ready=[]
 while visits and shots and (budget or ready):
  visits-=1
  if batch and not ready and budget>=4 and visits+1>=2:
   planned=[]
   for j in range(min(8,budget//2,visits+1,len(shots))):
    s=shots[(cursor%len(shots)+j)%len(shots)]
    if not s['split'] or not s['step']:break
    planned.append(s)
   if len(planned)>=2:
    ready=[s['id'] for s in planned];c=sum(s['cost'] for s in planned);calls+=c;budget-=c
  i=cursor%len(shots);s=shots[i]
  if not s['step']:cursor+=1;continue
  if ready:assert ready.pop(0)==s['id']
  else:
   if budget<(2 if s['split'] else 1):cursor+=1;continue
   calls+=s['cost'];budget-=s['cost']
  trace.append((s['id'],s['ok']))
  if s['ok'] and s['erase']:shots.pop(i);cursor=i
  else:cursor+=1
 assert not ready and 0<=budget<=64 and calls<=64
 return trace,[s['id'] for s in shots],cursor,budget,calls
shot_cases=0
for budget in range(65):
 for _ in range(120):
  data=[]
  for i in range(rng.randrange(1,60)):
   split=rng.random()>.15;data.append(dict(id=i,split=split,step=rng.random()>.15,cost=(rng.choice([1,2]) if split else 1),ok=rng.random()>.12,erase=rng.random()>.45))
  c=rng.randrange(1000);assert shots_run(data,c,budget,False)==shots_run(data,c,budget,True),(budget,data)
  shot_cases+=1

def schedule(rows,budget,batch,fail=False,shadow=False):
 trace=[];actual=0;allowed=True
 for ji,paths in enumerate(rows):
  cursor=used=0
  while cursor<len(paths) and budget and used<8:
   n=0
   if batch and allowed and budget>=3 and used<7:
    while n<min(8-used,budget-1) and cursor+n<len(paths) and paths[cursor+n]=='v':n+=1
   if n>=2:
    budget-=1;actual+=1
    if fail or shadow:
     if fail:allowed=False
     budget-=n;actual+=n
    else:budget-=n-1
    trace.extend((ji,x) for x in range(cursor,cursor+n));cursor+=n;used+=n;continue
   required=2 if paths[cursor]=='c' else 1
   if budget<required:break
   budget-=required;actual+=required;trace.append((ji,cursor));cursor+=1;used+=1
  if not budget:break
 assert 0<=budget<=64 and actual<=64
 return trace,actual
schedule_cases=0
for budget in range(65):
 for _ in range(80):
  rows=[[rng.choice('vvvsc') for _ in range(rng.randrange(1,40))] for _ in range(rng.randrange(1,20))]
  oldtrace,oldcalls=schedule(rows,budget,False);trace,calls=schedule(rows,budget,True)
  assert trace==oldtrace and calls<=oldcalls
  for failure,shadow in [(True,False),(False,True)]:schedule(rows,budget,True,failure,shadow)
  schedule_cases+=3
high=[['v']*8 for _ in range(8)];a=schedule(high,64,True);assert len(a[0])==64 and a[1]<64

# 实际新报告类的AST路由：分块报告、空名单、单项拒绝和未知标签，未调用引擎。
report_vm=VM(norm(text(ROOT/'native/NativeMultiContact.cpp')))
report_class=next(n for n in report_vm.nodes('class_specifier') if report_vm.txt(n.child_by_field_name('name'))=='RangedReport')
def report_body(name):
 return next(n.child_by_field_name('body') for n in report_vm.nodes('function_definition') if report_class.start_byte<n.start_byte<n.end_byte<report_class.end_byte and re.search(r'\b'+name+r'\s*\(',report_vm.source[n.start_byte:n.child_by_field_name('body').start_byte].decode()))
find_body=report_body('Find');ray_body=report_body('onRaycastQuery');sweep_body=report_body('onSweepQuery');callback_cases=0
class Slot:pass
for slot_index,n,fail in itertools.product(range(8),[0,1,63,64,65,513],[-1,0,17]):
 slots=[Slot() for _ in range(8)];received=[]
 for q in slots:
  q.ray=NS(onHit=lambda value:received.append(value) is None and (fail<0 or value!=fail))
  q.sweep=NS(onEvent=lambda count,hits:received.extend(hits[:count]) is None and fail<0)
 env=dict(slots=slots,count=8,bad=False,tag=slots[slot_index],n=n,hits=list(range(n)),NX_SQR_CONTINUE=0,NX_SQR_ABORT_QUERY=1,NX_SQR_ABORT_ALL_QUERIES=2)
 env['Find']=lambda tag:execute(report_vm,find_body,dict(env,tag=tag))
 got=execute(report_vm,ray_body,env);expected=1 if 0<=fail<n else 0
 assert got==expected and len(received)==(fail+1 if expected else n) and not env['bad']
 received.clear();got=execute(report_vm,sweep_body,env);assert got==(0 if fail<0 else 1) and len(received)==n
 callback_cases+=2
for body in [ray_body,sweep_body]:
 env=dict(slots=slots,count=8,bad=False,tag=object(),n=1,hits=[0],NX_SQR_CONTINUE=0,NX_SQR_ABORT_QUERY=1,NX_SQR_ABORT_ALL_QUERIES=2)
 env['Find']=lambda tag:execute(report_vm,find_body,dict(env,tag=tag))
 assert execute(report_vm,body,env)==2 and env['bad'];callback_cases+=1
# 原参考重试循环逐token未改：任何中途失败只推进原成功前缀；当前窗停批不影响下窗再次尝试。
marker_ref='for(unsigned i=0;i<count;++i){const Path& path=job.paths[job.cursor];'
def reference_loop(p):
 b=p.txt(p.body('TryCapsuleBatch'));start=b.index(marker_ref);end=b.index('        if(shadow){if(match)',start)
 return token_fragment(b[start:end])
assert reference_loop(cp)==reference_loop(old)
def world_clear(p):
 return next(n.child_by_field_name('body') for n in p.nodes('function_definition') if p.txt(n).startswith('void Clear(bool alive,const char* reason)'))
assert cp.tokens(world_clear(cp))==old.tokens(world_clear(old)) and tok(cp,'Tick')==tok(old,'Tick')

# callback/SDK声明、生命周期、配置与父子日志结构静态核对。
native=text(ROOT/'native/NativeMultiContact.cpp');combat=text(ROOT/'IrisCombat.cpp')
assert 'NX_SQE_ASYNCHRONOUS' not in native and 'NX_SQE_SYNCHRONOUS' in native
assert 'scene->overlapOBBShapes(box,NX_ALL_SHAPES,64,buffer,&collector,groups,0,true)' in native
assert 'owner.query->linearCapsuleSweep(s.capsule,s.travel,NX_SF_STATICS|NX_SF_DYNAMICS|NX_SF_ALL_HITS,groups,0,&s);' in native
assert 'owner.query->raycastAllShapes(s.rayValue,NX_ALL_SHAPES,groups&NATIVE_BOLT_GROUPS,s.distance,NX_RAYCAST_SHAPE|NX_RAYCAST_DISTANCE,0,&s);' in native
assert 'owner.pending=true;++queryCalls;' in native and 'releaseSceneQuery(*query)' in native
assert 'PlannedJobCost' not in combat and 'batchSpare' not in combat
assert 'if(!complete){' in cp.txt(cp.body('TryCapsuleBatch')) and 'allowBatch=false' in cp.txt(cp.body('TryCapsuleBatch'))
for name in ['Collector','TerrainRayCollector','CylinderCollector']:
 def cls(p):
  node=next(n for n in p.nodes('class_specifier') if p.txt(n.child_by_field_name('name'))==name);return p.tokens(node)
 assert cls(np)==cls(on),name
sdk=text(ROOT/'native/physx284/SDKs/Physics/include/NxSceneQuery.h')
assert 'always returns 0 when NX_SF_ALL_HITS is used' in sdk
assert 'void* userData=NULL' in sdk
cfg=configparser.ConfigParser();cfg.read(ROOT/'distribution/IrisArsenal.ini',encoding='utf8');assert cfg['IrisArsenal']['EnableRangedQueryBatching']=='1'
other=configparser.ConfigParser();other.read(ROOT/'package/IrisArsenal/IrisArsenal.ini',encoding='utf8');assert dict(cfg['IrisArsenal'])==dict(other['IrisArsenal'])
syntax=[]
for f in list(ROOT.glob('*.cpp'))+list(ROOT.glob('*.h'))+list((ROOT/'native').glob('*.cpp'))+list((ROOT/'native').glob('*.h')):
 s=norm(text(f));s=re.sub(r'typedef Item\*\(RootObjectFactory::\* CreateMember\)\([^;]+;','typedef void* CreateMember;',s);Program(s);syntax.append(str(f.relative_to(ROOT)))
for p in [ROOT/'tools/stage_package.py',ROOT/'tools/test_update_mod.py']:ast.parse(text(p))
diag=text(ROOT/'IrisDiagnostics.cpp');hd=text(ROOT/'IrisDiagnostics.h')
for enum,array in [('Kind','names'),('Counter','counters')]:
 enums=re.search('enum '+enum+r' \{([^}]+)\}',hd)[1].split(',')[:-1];names=re.findall(r'"[^"]+"',re.search(array+r'\[[A-Z_]+\]=\{([^}]+)\}',diag)[1]);assert len(enums)==len(names)
result=dict(callback_actual_AST_cases=callback_cases,capsule_actual_AST_cases=cases,prepare_actual_AST_cases=prepare,shot_schedule_equivalence_cases=shot_cases,capsule_schedule_cases=schedule_cases,high_pressure_64_paths_actual_scene_calls=a[1],protected_combat_functions=protected,syntax_units=syntax,medical_reentry_FIFO_specs=replay(text(ROOT/'IrisCombat.cpp')),SDK_and_collectors_checked=True,compiled=False,PhysX_or_game_or_threads_executed=False,FPS_measured=False)
args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False))
