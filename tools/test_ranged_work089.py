"""089非编译验收：解释实际C++控制流；SDK用确定性值替身，不冒称真实PhysX/线程/游戏测试。"""
from pathlib import Path
from types import SimpleNamespace as NS
import argparse,copy,hashlib,itertools,json,math,random,re,struct,sys,configparser,ast
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from test_native_profile084 import Eval,definitions,free_body
from test_performance080 import Program,Returned
from test_medical_gate083 import replay
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
   self.assign(l,e,copy.deepcopy(v) if isinstance(v,Diag) else v);return v
  if k=='binary_expression':
   l=n.child_by_field_name('left');r=n.child_by_field_name('right');op=self.source[l.end_byte:r.start_byte].decode().strip()
   if op in ('&','|','<<'):
    a,b=self.expr(l,e),self.expr(r,e);return {'&':lambda:a&b,'|':lambda:a|b,'<<':lambda:a<<b}[op]()
  if k=='call_expression':
   name=self.txt(n.child_by_field_name('function'));args=n.child_by_field_name('arguments').named_children
   if name.startswith('static_cast<'):return self.expr(args[0],e)
   if name=='ReadObjectKey':
    shape,key=self.expr(args[0],e),self.expr(args[1],e)
    if shape=='bad':self.assign(args[2].named_children[-1] if args[2].type=='pointer_expression' else args[2],e,0xc0000005);return False
    key.present=shape is not None;key.type=shape;return True
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
    elif '[' in self.txt(d):value=[e[typ](i) if typ=='RangedSlot' else None for i in range(8 if typ=='RangedSlot' else 64)]
    else:value=e[typ]() if typ in e and callable(e[typ]) else 0
    e[name]=value
   return
  return super().statement(n,e)
 def run_body(self,b,e):
  try:self.statement(b,e)
  except Returned as r:return r.value
def main(before,out):
 native=VM(norm(txt(ROOT/'native/NativeMultiContact.cpp')));combat=Program(txt(ROOT/'IrisCombat.cpp'))
 oldn=Program(norm(txt(before/'native/NativeMultiContact.cpp')));oldc=Program(txt(before/'IrisCombat.cpp'))
 protected=0
 for old,new,skip in [(oldn,native,{'RangedBatch'}),(oldc,combat,{'Configure','RunRangedBatch','PrepareShotBatch','ResolveJobs','AdvanceEffects'})]:
  for node in old.nodes('function_definition'):
   b=node.child_by_field_name('body');header=old.source[node.start_byte:b.start_byte].decode()
   if any(re.search(r'\b'+x+r'\s*\(',header) for x in skip):continue
   match=[n.child_by_field_name('body') for n in new.nodes('function_definition') if new.source[n.start_byte:n.child_by_field_name('body').start_byte].decode()==header]
   assert match,(header,len(match));assert any(old.tokens(b)==new.tokens(q) for q in match),header;protected+=1
 # 实际消费、位置推进、独立攻击与调度完整函数只允许这些接口替换。
 for name in ('ResolveJobs','PrepareShotBatch','AdvanceEffects'):
  s=combat.txt(combat.body(name)).replace('bool allowEmpty=true;','').replace('PrepareShotBatch(w,visits+1,budget,allowEmpty)','PrepareShotBatch(w,visits+1,budget)').replace('RunRangedBatch(w,shotBatchWork,count,budget,&allowEmpty)','RunRangedBatch(w,shotBatchWork,count,budget)').replace('RangedValue(beamBatchWork,next++)','beamBatchWork.results[next++]').replace('RangedValue(shotBatchWork,next++)','shotBatchWork.results[next++]')
  probe=Program('void X()'+s);assert probe.tokens(probe.body('X'))==oldc.tokens(oldc.body(name)),name
 # 解释实际函数，外部调用替身只提供SDK值，不重写产品分支。
 bodies={x:definitions(native,x) for x in ('SameRangedFloat','SameRangedInput','RangedSweepBounds','RangedBoundsVolume','ProbeRangedEmpty','RangedBatch')}
 cb=next(n for n in native.nodes('class_specifier') if native.txt(n.child_by_field_name('name'))=='RangedEmptyReport')
 callback=next(n.child_by_field_name('body') for n in native.nodes('function_definition') if cb.start_byte<n.start_byte<n.end_byte<cb.end_byte and 'onEvent(' in native.source[n.start_byte:n.child_by_field_name('body').start_byte].decode())
 env={'unsigned':int,'double':float,'float':f32,'std::min':min,'std::max':max,'fabs':abs,'_finite':math.isfinite,'Finite':math.isfinite,'FLT_EPSILON':2**-23,'FLT_MAX':f32(3.4028234663852886e38),'CHARACTER':11,'NxBounds3':Box,'NxVec3':Vec,'ObjectKey':lambda:NS(present=False,type=0),'NX_ALL_SHAPES':3,'IrisDiagnostics::RANGED_EMPTY_PROBE':0}
 env['std::memcmp']=lambda a,b,n:0 if struct.pack('<f',a)==struct.pack('<f',b) else 1
 def call(name,**kw):return native.run_body(bodies[name],dict(env,**kw))
 env['SameRangedFloat']=lambda a,b:call('SameRangedFloat',a=a,b=b)
 env['SameRangedInput']=lambda a,b:call('SameRangedInput',a=a,b=b)
 env['RangedSweepBounds']=lambda p,box:call('RangedSweepBounds',p=p,box=box)
 env['RangedBoundsVolume']=lambda box:call('RangedBoundsVolume',box=box)
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
   for i in range(0,len(self.broad),n):
    data=self.broad[i:i+n]
    if not r.onEvent(len(data),data):break
   return len(self.broad)
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
  scene=Scene(rows,broad);results=[NS(characters=contacts(i),terrain=contacts(i)) for i in range(len(rows))]
  audit=NS(**dict.fromkeys(FIELDS,0));owner=NS(scene=scene,query=None,pending=False,Finish=scene.Finish)
  e=dict(env,world=scene,scene=scene,rows=rows,paths=[r['p'] for r in rows],count=len(rows),groups=0xffffffff,results=results,queryCalls=0,policy=policy,audit=audit,
   Initialize=lambda:True,getSdk=lambda:scene.sdk,RANGED_BATCH_CAPACITY=8,RangedAudit=lambda:NS(**dict.fromkeys(FIELDS,0)),RangedSlot=slot,RangedReport=lambda s,n:NS(bad=False),RangedQueryOwner=lambda s:owner,NxSceneQueryDesc=lambda:NS(report=None,executeMode=0),Diagnostic=diag,NxRay=lambda a,b:NS(origin=a,dir=b),TerrainRayCollector=lambda out,*args:NS(out=out,status=0),Collector=lambda out,*args:NS(out=out,status=0),NxSphere=lambda:NS(center=Vec(),radius=0),NX_SQE_SYNCHRONOUS=0,NX_RAYCAST_SHAPE=1,NX_RAYCAST_DISTANCE=2,NATIVE_BOLT_GROUPS=0x087fde47,NX_SF_STATICS=1,NX_SF_DYNAMICS=2,NX_SF_ALL_HITS=4,ISSUE_NONE=0,ISSUE_BATCH_INPUT=1,QUERY_COMPLETE=0,QUERY_INVALID=3,FinalizeSweep=lambda out,status:status)
  for name in ['DetailsEnabled','CollisionProfileEnabled']:e['IrisDiagnostics::'+name]=lambda:False
  for name in ['RANGED_REUSE_LOOKUP','RANGED_BATCH_CREATE','RANGED_BATCH_RAYS','RANGED_BATCH_BODIES']:e['IrisDiagnostics::'+name]=0
  def probe(*args):
   local=dict(e,scene=args[0],paths=args[1],count=args[2],mask=args[3],groups=args[4],calls=e['queryCalls'],policy=args[6],audit=args[7])
   ret=native.run_body(bodies['ProbeRangedEmpty'],local);e['queryCalls']=local['calls'];return ret
  e['ProbeRangedEmpty']=probe
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
  for kind in ('RANGED_REUSE_LOOKUP','RANGED_EMPTY_PROBE'):
   assert dvm.run_body(activeBody,dict(e,k=kindNames.index(kind)))==all([enabled,performance,details,collision]);gateCases+=1
 ctor=definitions(dvm,'Scope');assert 'if(active)' in dvm.txt(ctor) and 'begin=Now()' in dvm.txt(ctor)
 for f in ('distribution/IrisArsenal.ini','package/IrisArsenal/IrisArsenal.ini'):
  c=configparser.ConfigParser();c.read(ROOT/f,encoding='utf8');assert c['IrisArsenal']['EnableRangedQueryReuse']=='1' and c['IrisArsenal']['EnableRangedEmptyPruning']=='1' and c['IrisArsenal']['EnableRangedEmptyShadow']=='0'
 for f in ('tools/stage_package.py','tools/test_update_mod.py',__file__):ast.parse(txt(Path(f) if str(f)==__file__ else ROOT/f))
 result=dict(actual_CPP_AST_batches=cases+extra+2,exact_key_fields_and_signed_zero=keycases+2,swept_sphere_envelope_samples=bounds,streaming_callback_cases=callbacks,mock_empty_sweeps_saved=saved,protected_original_functions=protected,actual_logging_gate_cases=gateCases,full_AdvanceEffects_ResolveJobs_consumer_tokens_preserved=True,syntax_units=syntax,medical_FIFO_specs=replay(txt(ROOT/'IrisCombat.cpp')),compiled=False,real_PhysX_or_threads_or_game_tested=False,FPS_measured=False)
 out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--before',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();main(a.before,a.out)
