"""094非编译验收：公开接口模式、实际C++ AST、保守包含与异常不重查。SDK为纯值替身。"""
from pathlib import Path
from types import SimpleNamespace as NS
import sys,math,random,copy,json,re,hashlib,configparser,ast,argparse
T=Path(__file__).parent;R=Path(__file__).resolve().parents[1] if T.name=='tools' else Path('E:/KenshiProject/2.Projects/IrisArsenal');BASELINE=T/'baseline';OUTPUT=T/'validation094.json';sys.path.insert(0,str(R/'tools'))
from test_spatial_projectiles090 import VM as BaseVM,Vec as OldVec,norm,Box as OldBox
from test_performance080 import Program,Returned,tree_sitter,tree_sitter_cpp
from test_native_profile084 import definitions
from test_query_boundary093 import strip_observers

class Vec(OldVec):
 def __add__(self,b):return Vec(*(x+y for x,y in zip(self,b)))
 def __sub__(self,b):return Vec(*(x-y for x,y in zip(self,b)))
 def __mul__(self,b):return Vec(*(x*b for x in self))
 def magnitudeSquared(self):return sum(x*x for x in self)
 def cross(self,a,b):self[:]=[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
 def normalize(self):self[:]=[x/self.magnitude() for x in self]
class Box(OldBox):
 def include(self,p):self.min=Vec(*(min(x,y) for x,y in zip(self.min,p)));self.max=Vec(*(max(x,y) for x,y in zip(self.max,p)))
 def fatten(self,r):self.min=Vec(*(x-r for x in self.min));self.max=Vec(*(x+r for x in self.max))
 def intersects(self,b):return all(x<=v and u<=y for x,y,u,v in zip(self.min,self.max,b.min,b.max))
class Diagnostic(NS):
 def __init__(self):super().__init__(**dict.fromkeys('issue received uniqueBeforeFailure missingPoints hitIndex rawFraction fractionBits identityException recoveredInitial identityComparisons identityProbes identityDuplicates identityTables bodyBufferGrowth approximateKind skippedIdentity skippedGeometry skippedCapacity skippedInput candidates characters shapeTests shapeTypes geometryException conservative'.split(),0))
class Contacts:
 def __init__(self,fail=-1):self.items=[];self.count=0;self.diagnostic=Diagnostic();self.fail=fail
 def Append(self,c):
  if c.object.index==self.fail:return False
  self.items.append(copy.deepcopy(c));self.count+=1;return True
class Index:
 def __init__(self,o):self.o=o
 def Find(self,key):
  for i,c in enumerate(self.o.items):
   if vars(c.object)==vars(key):return i
  return self.o.count
 def Committed(self):pass
class VM(BaseVM):
 def expr(self,n,e):
  if n.type=='call_expression' and self.txt(n.child_by_field_name('function'))=='std::swap':
   a,b=n.child_by_field_name('arguments').named_children;x,y=self.expr(a,e),self.expr(b,e);self.assign(a,e,y);self.assign(b,e,x);return
  return super().expr(n,e)
 def statement(self,n,e):
  if n.type=='declaration':
   typ=self.txt(n.child_by_field_name('type'))
   if typ in ['NxCapsule','ConservativeCapsuleMap','NxBounds3']:
    for item in n.named_children:
     if item.type in ('primitive_type','type_identifier','qualified_identifier','type_qualifier'):continue
     d=item.child_by_field_name('declarator') if item.type=='init_declarator' else item
     name=re.findall(r'\b\w+\b',self.txt(d))[0]
     if d.type=='array_declarator':e[name]=[e[typ]() for _ in range(8)]
     elif d.type=='reference_declarator':e[name]=self.expr(item.child_by_field_name('value'),e)
     else:e[name]=e[typ]()
    return
   if typ=='Diagnostic' and 'empty=' in self.txt(n):e['empty']=Diagnostic();return
   if typ=='BatchDiagnostic' and 'clean=' in self.txt(n):e['clean']=Diagnostic();return
  if n.type=='try_statement':
   body=next(x for x in n.named_children if x.type=='compound_statement')
   try:self.statement(body,e)
   except MemoryError:
    handler=next(x for x in n.named_children if x.type=='catch_clause');self.statement(handler.child_by_field_name('body'),e)
   return
  return super().statement(n,e)
 def assign(self,n,e,v):
  if n.type=='identifier' and self.txt(n) in ['mapped','diagnostic'] and self.txt(n) in e and isinstance(e[self.txt(n)],NS):vars(e[self.txt(n)]).update(copy.deepcopy(vars(v)));return
  return super().assign(n,e,v)

def main():
 native=(R/'native/NativeMultiContact.cpp').read_text('utf8');v=VM(norm(strip_observers(native)))
 env={'unsigned':int,'double':float,'float':float,'std::min':min,'std::max':max,'fabs':abs,'fabsf':abs,'Finite':math.isfinite,'DBL_EPSILON':2**-52,'FLT_EPSILON':2**-23,'NxSphere':lambda:NS(center=Vec(),radius=0),'NxCapsule':lambda:NS(p0=Vec(),p1=Vec(),radius=0),'ConservativeCapsuleMap':lambda:NS(origin=[0.]*3,inverse=[0.]*3,radius=0,parallel=0),'NxBounds3':Box}
 bodies={name:v.body(name) for name in ['MapExactCapsuleToExpandedAABBTest','ConservativeCapsuleIntersectsAABB','MapExactSphereToAABBQuery','MapExactCapsuleToAABBQuery','MapExactCylinderToConservativeOBB','OverlapCapsules']}
 def call(name,**kwargs):return v.run_body(bodies[name],dict(env,**kwargs))
 rng=random.Random(94015);mathCases=0
 for i in range(24000):
  a=Vec(*(rng.uniform(-10000,10000) for _ in range(3)));b=a+Vec(*(rng.uniform(-180,180) for _ in range(3)));r=rng.uniform(.01,120)
  if i%7==0:b=Vec(*a)
  elif i%7==1:b[1]=a[1]
  capsule=NS(p0=a,p1=b,radius=r);mapped=env['ConservativeCapsuleMap']();call('MapExactCapsuleToExpandedAABBTest',exact=capsule,mapped=mapped)
  t=rng.random();c=a+(b-a)*t;sr=rng.uniform(.001,15);offset=Vec(*(rng.uniform(-r-sr,r+sr) for _ in range(3)));c=c+offset
  box=Box();box.min=c-Vec(sr,sr,sr);box.max=c+Vec(sr,sr,sr)
  d=b-a;den=d.magnitudeSquared();t=max(0.,min(1.,sum((c[k]-a[k])*d[k] for k in range(3))/den)) if den else 0.
  exact=(c-(a+d*t)).magnitudeSquared()<=(r+sr)**2
  approx=call('ConservativeCapsuleIntersectsAABB',mapped=mapped,bounds=box)
  assert not exact or approx,(i,a,b,r,c,sr)
  mathCases+=1
 # 端点、平行、退化球、同t约束（不能独立三个轴各自命中）、精确切触和负坐标。
 edgeCases=0
 for a,b in [(Vec(0,0,0),Vec(0,0,0)),(Vec(-50,0,0),Vec(50,0,0)),(Vec(-50,-50,-50),Vec(50,50,50))]:
  for r in [.001,1,25,120]:
   mapped=env['ConservativeCapsuleMap']();call('MapExactCapsuleToExpandedAABBTest',exact=NS(p0=a,p1=b,radius=r),mapped=mapped)
   for t in [0,.5,1]:
    c=a+(b-a)*t;box=Box();box.min=c+Vec(0,r,0);box.max=box.min+Vec(1,1,1)
    assert call('ConservativeCapsuleIntersectsAABB',mapped=mapped,bounds=box);edgeCases+=1
 mapped=env['ConservativeCapsuleMap']();call('MapExactCapsuleToExpandedAABBTest',exact=NS(p0=Vec(0,0,0),p1=Vec(10,10,0),radius=.1),mapped=mapped)
 box=Box();box.min=Vec(0,9,0);box.max=Vec(1,10,1);assert not call('ConservativeCapsuleIntersectsAABB',mapped=mapped,bounds=box);edgeCases+=1
 # 实际sphere/capsule映射保持原体积参数；圆柱映射只在原定向盒向外加余量，不重复创建基。
 for i in range(300):
  c=NS(x=rng.uniform(-1e5,1e5),y=rng.uniform(-1e5,1e5),z=rng.uniform(-1e5,1e5));r=rng.uniform(.1,120)
  sphere=env['NxSphere']();call('MapExactSphereToAABBQuery',center=c,radius=r,mapped=sphere);assert sphere.center==[c.x,c.y,c.z] and sphere.radius==r
  cap=env['NxCapsule']()
  # 参数名from是C++标识符，使用kwargs传给解释器。
  call('MapExactCapsuleToAABBQuery',**{'from':c,'to':c,'radius':r,'mapped':cap});assert cap.p0==sphere.center and cap.p1==sphere.center and cap.radius==r
  exactBox=NS(center=Vec(c.x,c.y,c.z),extents=Vec(r,r,5000),rot='original_basis');mappedBox=NS()
  call('MapExactCylinderToConservativeOBB',exact=exactBox,mapped=mappedBox);assert mappedBox.rot==exactBox.rot and mappedBox.center==exactBox.center and all(x>=y for x,y in zip(mappedBox.extents,exactBox.extents))
 # 真实OverlapCapsules函数AST：SDK只做一次候选查询，逐形体精确函数在新模式不可达。
 class Candidates:
  def __init__(self,d):self.count=0;self.status=0;self.d=d;self.items=[]
  def At(self,k):return self.items[k]
 class Scene:
  def __init__(self,shapes):self.shapes=shapes;self.commands=0;self.sdk=object()
  def getPhysicsSDK(self):return self.sdk
  def overlapAABBShapes(self,b,typ,n,chunk,c,groups,mask,accurate):
   assert not accurate;self.commands+=1
   for sh in self.shapes:
    if sh is None:c.d.skippedGeometry+=1;continue
    if sh=='bad':c.d.skippedIdentity+=1;continue
    if sh.box.intersects(b):c.items.append(NS(shape=sh,key=NS(present=True,type=11,container=9,containerSerial=1,index=sh.identity,serial=1),bounds=Box(),typeBit=0,hitMask=0));c.d.characters+=1
   c.count=len(c.items);c.d.candidates=len(self.shapes)
 originalExpr=VM.expr
 def expr(self,n,e):
  if n.type=='call_expression':
   name=self.txt(n.child_by_field_name('function'));args=n.child_by_field_name('arguments').named_children
   if name=='ReadCapsuleGeometry':
    shape=self.expr(args[0],e)
    if getattr(shape,'badGeometry',False):return False
    self.assign(args[1],e,shape.kind);self.assign(args[2],e,copy.deepcopy(shape.box));return True
   if name=='CheckCapsuleGeometry':raise AssertionError('unexpected precise geometry call')
  return originalExpr(self,n,e)
 VM.expr=expr
 def batch(paths,shapes,fail=-1):
  scene=Scene(shapes);out=[Contacts(fail) for _ in paths];d=Diagnostic();e=dict(env,world=scene,paths=paths,count=len(paths),groups=0xffffffff,results=out,diagnostic=d,queryCalls=0,conservativeQueries=True,
    BatchDiagnostic=Diagnostic,Diagnostic=Diagnostic,Initialize=lambda:True,getSdk=lambda:scene.sdk,QUERY_COMPLETE=0,QUERY_INVALID=3,QUERY_NOT_READY=4,QUERY_UNSUPPORTED=1,QUERY_OVERFLOW=2,CAPSULE_BATCH_CAPACITY=8,
    ISSUE_NONE=0,ISSUE_BATCH_INPUT=1,ISSUE_INPUT_RADIUS=2,ISSUE_INPUT_ORIGIN=3,ISSUE_INPUT_SCENE=4,ISSUE_CAPACITY=5,ISSUE_BATCH_SHAPE=6,
    NX_ALL_SHAPES=3,NX_SHAPE_SPHERE=0,NX_SHAPE_CAPSULE=1,NX_SHAPE_BOX=2,NX_SHAPE_CONVEX=3,CapsuleCandidates=Candidates,IdentityIndex=Index,
    Contact=lambda:NS(point=Vec()),**{'std::numeric_limits<unsigned>::max':lambda:2**32-1})
  e['MapExactCapsuleToExpandedAABBTest']=lambda exact,mapped:call('MapExactCapsuleToExpandedAABBTest',exact=exact,mapped=mapped)
  e['ConservativeCapsuleIntersectsAABB']=lambda mapped,bounds:call('ConservativeCapsuleIntersectsAABB',mapped=mapped,bounds=bounds)
  status=v.run_body(bodies['OverlapCapsules'],e);return status,out,d,scene.commands
 batchCases=0
 for n in [2,4,8]:
  paths=[NS(from_=None,to=NS(x=10,y=0,z=0),radius=1) for _ in range(n)]
  for p in paths:setattr(p,'from',NS(x=0,y=0,z=0))
  shapes=[]
  for i in range(650):
   b=Box();b.min=Vec(rng.uniform(-5,15),rng.uniform(-4,4),rng.uniform(-4,4));b.max=b.min+Vec(1,1,1)
   shapes.append(NS(box=b,identity=i//2,kind=99 if i%5==0 else 0,badGeometry=i%101==0))
  # 全部类型均可使用合法AABB；坏身份/坏形体不得导致额外场景查询或清空正常名单。
  shapes+=['bad',None]
  for fail in [-1,3]:
   status,out,d,queries=batch(paths,shapes,fail);assert status==0 and queries==1 and d.skippedIdentity==1 and d.skippedGeometry>0
   for result in out:assert result.count==len({x.object.index for x in result.items}) and all(x.object.index!=fail for x in result.items)
   batchCases+=1
  paths[-1].radius=float('nan');status,out,d,queries=batch(paths,shapes);assert status==0 and queries==1 and not out[-1].count and d.skippedInput==1;batchCases+=1
  for p in paths:p.radius=float('nan')
  status,out,d,queries=batch(paths,shapes);assert status==0 and queries==0 and not any(r.count for r in out) and d.skippedInput==n;batchCases+=1
 # 旧256结果/512候选不再是上限，正常有520个独立身份全部保留。
 paths=[NS(to=NS(x=10,y=0,z=0),radius=1) for _ in range(2)]
 for p in paths:setattr(p,'from',NS(x=0,y=0,z=0))
 b=Box();b.min=Vec(0,0,0);b.max=Vec(1,1,1)
 dense=[NS(box=b,identity=i,kind=99,badGeometry=False) for i in range(520)]
 status,out,d,queries=batch(paths,dense);assert status==0 and queries==1 and all(r.count==520 for r in out);batchCases+=1
 status,out,d,queries=batch(paths,[]);assert status==0 and queries==1 and not any(r.count for r in out);batchCases+=1
 # 实际OverlapCollector回调AST；坏身份/空形体/容量失败/哈希冲突后的有效项继续。
 classNode=next(x for x in v.nodes('class_specifier') if v.txt(x.child_by_field_name('name'))=='OverlapCollector')
 collectorVM=VM(v.txt(classNode)+';');collectorBody=collectorVM.body('onEvent')
 originalCollectorExpr=collectorVM.expr
 def collectorExpr(n,e):
  if n.type=='call_expression' and collectorVM.txt(n.child_by_field_name('function'))=='ReadObjectKey':
   args=n.child_by_field_name('arguments').named_children;shape=collectorVM.expr(args[0],e)
   if shape=='bad':return False
   key=collectorVM.expr(args[1],e);vars(key).update(copy.deepcopy(vars(shape)));return True
  if n.type=='call_expression' and collectorVM.txt(n.child_by_field_name('function'))=='unsigned':return int(collectorVM.expr(n.child_by_field_name('arguments').named_children[0],e))
  return originalCollectorExpr(n,e)
 collectorVM.expr=collectorExpr
 class FailureIndex(Index):
  def Find(self,key):return 2**32-1 if key.index==-2 else super().Find(key)
 key=lambda i:NS(type=11,present=True,container=9,containerSerial=1,index=i,serial=1)
 out=Contacts(3);shapes=[None,'bad',key(1),key(3),key(1),key(-2),key(2)]
 e=dict(env,output=out,approximate=True,status=0,identities=FailureIndex(out),count=len(shapes),shapes=shapes,ObjectKey=lambda:NS(),Contact=lambda:NS(point=Vec()),CHARACTER=11,
  ISSUE_HIT_SHAPE=1,ISSUE_KEY_READ=2,ISSUE_CAPACITY=3,QUERY_OVERFLOW=2,**{'std::numeric_limits<unsigned>::max':lambda:2**32-1})
 assert collectorVM.run_body(collectorBody,e) is True and e['status']==0 and [c.object.index for c in out.items]==[1,2]
 assert (out.diagnostic.skippedGeometry,out.diagnostic.skippedIdentity,out.diagnostic.skippedCapacity)==(1,1,2)
 callbackCases=1
 # 实际公开查询调用分支：新模式false/旧模式true，各只调用一次；坏数据新模式0查询且consume为空。
 class SphereScene:
  def __init__(self):self.flags=[];self.sdk=object()
  def getPhysicsSDK(self):return self.sdk
  def overlapSphereShapes(self,s,typ,n,chunk,collector,groups,mask,accurate):self.flags.append(accurate)
  def overlapCapsuleShapes(self,s,typ,n,chunk,collector,groups,mask,accurate):self.flags.append(accurate)
 queryCases=0
 for name in ['OverlapSphere','OverlapCapsule']:
  for conservative in [False,True]:
   for bad in [False,True]:
    scene=SphereScene();result=Contacts();kwargs=dict(env,world=scene,result=result,queryCalls=0,conservativeQueries=conservative,Initialize=lambda:True,getSdk=lambda:scene.sdk,
     radius=float('nan') if bad else 1,groups=0xffffffff,OverlapCollector=lambda r,loose:NS(status=0),Diagnostic=Diagnostic,NX_ALL_SHAPES=3,
     ISSUE_NONE=0,ISSUE_INPUT_RADIUS=1,ISSUE_INPUT_ORIGIN=2,ISSUE_INPUT_SCENE=3,QUERY_COMPLETE=0,QUERY_INVALID=3,QUERY_NOT_READY=4,QUERY_UNSUPPORTED=1)
    kwargs.update({'from':NS(x=0,y=0,z=0),'to':NS(x=10,y=0,z=0),'center':NS(x=0,y=0,z=0)})
    kwargs['MapExactSphereToAABBQuery']=lambda center,radius,mapped:call('MapExactSphereToAABBQuery',center=center,radius=radius,mapped=mapped)
    kwargs['MapExactCapsuleToAABBQuery']=lambda a,b,r,m:call('MapExactCapsuleToAABBQuery',**{'from':a,'to':b,'radius':r,'mapped':m})
    status=v.run_body(v.body(name),kwargs)
    assert scene.flags==([] if bad else [not conservative])
    assert status==(0 if not bad or conservative else 3)
    assert kwargs['queryCalls']==(0 if bad else 1)
    if bad and conservative:assert result.diagnostic.skippedInput==1
    queryCases+=1
 # 语法/保护链/工作量：飞弹、资格、逐段和医疗函数逐token不变，查询次数路径保持。
 before=BASELINE;protected={};grammar=[]
 for f in ['native/NativeMultiContact.cpp','native/NativeMultiContact.h','IrisCombat.cpp','IrisDiagnostics.cpp','IrisDiagnostics.h']:
  raw=(R/f).read_text('utf8');p=Program(norm(raw));grammar.append(f)
 for f,names in [('native/NativeMultiContact.cpp',['ReadObjectKey','SweepAll','ProjectileAll','RayBlocker','FinalizeSweep','BodyGeometry','SameRangedInput','ProbeRangedEmpty','ProbeRangedSpatial','BuildRangedSpatialGroups']),('IrisCombat.cpp',['DamageTarget','Collect','Flush','ResolveJobs','AdvanceEffects','Emit','Blast','RangedReady','PrepareShotBatch','PrepareBeamBatch'])]:
  a=Program(norm(strip_observers((before/f).read_text('utf8'))));b=Program(norm(strip_observers((R/f).read_text('utf8'))))
  for name in names:
   headers=lambda p:[n for n in p.nodes('function_definition') if re.search(r'\b'+name+r'\s*\(',p.source[n.start_byte:n.child_by_field_name('body').start_byte].decode())]
   aa,bb=headers(a),headers(b)
   assert len(aa)==len(bb),(name,len(aa),len(bb))
   for x,y in zip(aa,bb):assert a.tokens(x.child_by_field_name('body'))==b.tokens(y.child_by_field_name('body')),name
   if aa:protected[f+':'+name]=len(aa)
 # 新开关缺项0，关闭无额外时钟；一次汇总只有一个Guard，回调没有日志/医疗调用。
 diag=(R/'IrisDiagnostics.cpp').read_text('utf8');p=Program(norm(diag))
 assert 'Switch(ini,L"EnableConservativeQueryLogging",false)' in diag
 record=p.txt(p.body('RecordConservativeQuery'));assert record.index('if(!ConservativeQueryLoggingEnabled()')<record.index('Guard guard') and record.count('Guard guard')==1 and 'Now(' not in record
 combat=(R/'IrisCombat.cpp').read_text('utf8');cb=Program(combat);trybatch=cb.txt(cb.body('TryCapsuleBatch'))
 assert 'const bool shadow=!approximate&&' in trybatch and trybatch.index('if(!complete){QueryWait')<trybatch.index('if(!complete||shadow)')
 # 原SDK公开接口注释的证据必须仍存在；不是自造API或从新PhysX猜旧接口。
 sdk=(R/'native/physx284/SDKs/Physics/include/NxScene.h').read_text('utf8')
 assert sdk.count('false to test against the AABBs only')>=3
 for ini in ['distribution/IrisArsenal.ini','package/IrisArsenal/IrisArsenal.ini']:
  c=configparser.ConfigParser();c.read(R/ini,encoding='utf8');assert c['IrisArsenal']['EnableConservativeDamageQueries']=='1' and c['IrisArsenal']['EnableConservativeQueryLogging']=='1'
 for n in ['tools/stage_package.py','tools/test_update_mod.py']:ast.parse((R/n).read_text('utf8'))
 result=dict(actual_mapping_AST_cases=mathCases+edgeCases+900,random_capsule_superset_cases=mathCases,edges=edgeCases,actual_batch_AST_cases=batchCases,actual_callback_anomaly_cases=callbackCases,actual_query_policy_cases=queryCases,normal_batch_scene_queries=1,abnormal_item_whole_batch_requery=0,exact_shape_calls_new_batch=0,protected_functions=protected,grammar=grammar,compiler='not run by policy',runtime_PhysX='not run',FPS='not measured')
 OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--before',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
 BASELINE=args.before;OUTPUT=args.out;main()
