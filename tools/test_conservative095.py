"""095非编译验收：执行实际C++ AST；SDK只用值替身，不冒称原生性能。"""
from pathlib import Path
from types import SimpleNamespace as NS
from collections import Counter
import sys,re,json,math,random,copy,hashlib,ast,configparser,importlib.util
import argparse
R=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--before',type=Path,required=True);a.add_argument('--out',type=Path,required=True);args=a.parse_args();T=args.before;sys.path.insert(0,str(R/'tools'))
from test_conservative094 import VM,Vec,Box,Diagnostic,Contacts,Index
from test_query_boundary093 import strip_observers
from test_spatial_projectiles090 import norm,f32
from test_performance080 import Program

class CountVM(VM):
 def __init__(self,s):super().__init__(s);self.cost=Counter();self.nativeReads=Counter();self.cachedBodies={}
 def body(self,name):
  if name not in self.cachedBodies:self.cachedBodies[name]=super().body(name)
  return self.cachedBodies[name]
 def expr(self,n,e):
  if n.type=='binary_expression':
   a=n.child_by_field_name('left');b=n.child_by_field_name('right');op=self.source[a.end_byte:b.start_byte].decode().strip()
   self.cost[op]+=1
  if n.type=='call_expression':
   name=self.txt(n.child_by_field_name('function'));args=n.child_by_field_name('arguments').named_children
   if name in ['ReadCapsuleGeometry','ReadCapsuleBounds']:
    shape=self.expr(args[0],e)
    if name=='ReadCapsuleGeometry':self.nativeReads['getType']+=1
    self.nativeReads['getWorldBounds']+=1
    if getattr(shape,'badGeometry',False):return False
    if name=='ReadCapsuleGeometry':self.assign(args[1],e,shape.kind);out=args[2]
    else:out=args[1]
    self.assign(out,e,copy.deepcopy(shape.box));return True
   if name=='CheckCapsuleGeometry':raise AssertionError('普通近似不得重跑精确几何')
   if name=='IrisDiagnostics::ConservativeQueryLoggingEnabled':return False
  return super().expr(n,e)

src=(R/'native/NativeMultiContact.cpp').read_text('utf8');v=CountVM(norm(strip_observers(src)))
env={'unsigned':int,'double':float,'float':float,'std::min':min,'std::max':max,'fabs':abs,'fabsf':abs,'Finite':math.isfinite,
 'DBL_EPSILON':2**-52,'FLT_EPSILON':2**-23,'NxSphere':lambda:NS(center=Vec(),radius=0),
 'NxCapsule':lambda:NS(p0=Vec(),p1=Vec(),radius=0),'ConservativeCapsuleMap':lambda:NS(origin=[0.]*3,inverse=[0.]*3,radius=0,parallel=0),'NxBounds3':Box}
def call(name,**kw):return v.run_body(v.body(name),dict(env,**kw))
def mapping(a,b,r):
 m=env['ConservativeCapsuleMap']();call('MapExactCapsuleToExpandedAABBTest',exact=NS(p0=a,p1=b,radius=r),mapped=m);return m
def bounds(a,b,r):
 q=Box();q.setEmpty();q.include(a);q.include(b);q.fatten(r)
 scale=max(1,*map(abs,q.min),*map(abs,q.max));q.fatten(scale*(4*2**-23));return q
def predicate(name,m,b):
 v.cost.clear();answer=call(name,mapped=m,bounds=b);return answer,Counter(v.cost)

rng=random.Random(950025);cases=0;extras=0;deleted=Counter();per_parallel=Counter()
for i in range(12000):
 a=Vec(*(f32(rng.uniform(-35000,35000)) for _ in range(3)));b=a+Vec(*(f32(rng.uniform(-30,30)) for _ in range(3)))
 if i%4==0:b[0]=a[0]
 if i%4==1:b[0]=a[0];b[1]=a[1]
 if i%4==2:b=copy.deepcopy(a)
 r=f32(rng.uniform(.1,20));m=mapping(a,b,r);q=bounds(a,b,r)
 box=Box();box.min=a+Vec(*(f32(rng.uniform(-20,20)) for _ in range(3)));box.max=box.min+Vec(*(f32(rng.uniform(.1,8)) for _ in range(3)))
 if not q.intersects(box):continue
 old,c0=predicate('ConservativeCapsuleIntersectsAABBReference',m,box);new,c1=predicate('ConservativeCapsuleIntersectsAABB',m,box)
 assert not old or new,(i,a,b,r,box.min,box.max)
 extras+=int(new and not old);cases+=1
 # 效率定理适用条件：平行轴不是仅靠float外扩余量通过，故原代码不会在被删条件处返回。
 ordinary=all(not (m.parallel&(1<<j)) or box.min[j]-r<=a[j]<=box.max[j]+r for j in range(3))
 if ordinary:
  # 相同控制流下，新代码只删除语法节点；逐类操作不能增加。
  assert all(c1[k]<=c0[k] for k in set(c0)|set(c1)),(c0,c1,m.parallel)
  deleted.update(c0-c1);per_parallel[bin(m.parallel).count('1')]+=1

# 平行轴padding-only接触：允许仅在明确浮点外扩带多纳入，不能少。
a=Vec(0,0,0);b=Vec(10,0,0);m=mapping(a,b,1);q=bounds(a,b,1)
box=Box();box.min=Vec(2,1+1e-7,0);box.max=Vec(3,2,1)
assert q.intersects(box)
assert predicate('ConservativeCapsuleIntersectsAABBReference',m,box)[0] is False
assert predicate('ConservativeCapsuleIntersectsAABB',m,box)[0] is True

class Candidates:
 def __init__(self,d):self.d=d;self.items=[];self.count=0;self.status=0
 def At(self,k):return self.items[k]
class Scene:
 def __init__(self,shapes):self.shapes=shapes;self.sdk=object();self.commands=0
 def getPhysicsSDK(self):return self.sdk
 def overlapAABBShapes(self,b,typ,n,chunk,c,g,mask,accurate):
  assert not accurate;self.commands+=1
  for sh in self.shapes:
   c.d.candidates+=1
   if sh is None:c.d.skippedGeometry+=1;continue
   if sh=='bad':c.d.skippedIdentity+=1;continue
   if sh.box.intersects(b):c.items.append(NS(shape=sh,key=NS(present=True,type=11,container=9,containerSerial=1,index=sh.identity,serial=1),bounds=Box(),typeBit=0,hitMask=0));c.d.characters+=1
  c.count=len(c.items)

def batch(paths,shapes,reuse,fail=-1):
 scene=Scene(shapes);out=[Contacts(fail) for _ in paths];d=Diagnostic();v.nativeReads.clear()
 e=dict(env,world=scene,paths=paths,count=len(paths),groups=0xffffffff,results=out,diagnostic=d,queryCalls=0,conservativeQueries=True,conservativeKernelReuse=reuse,
  BatchDiagnostic=Diagnostic,Diagnostic=Diagnostic,Initialize=lambda:True,getSdk=lambda:scene.sdk,QUERY_COMPLETE=0,QUERY_INVALID=3,QUERY_NOT_READY=4,QUERY_UNSUPPORTED=1,QUERY_OVERFLOW=2,CAPSULE_BATCH_CAPACITY=8,
  ISSUE_NONE=0,ISSUE_BATCH_INPUT=1,ISSUE_INPUT_RADIUS=2,ISSUE_INPUT_ORIGIN=3,ISSUE_INPUT_SCENE=4,ISSUE_CAPACITY=5,ISSUE_BATCH_SHAPE=6,
  NX_ALL_SHAPES=3,NX_SHAPE_SPHERE=0,NX_SHAPE_CAPSULE=1,NX_SHAPE_BOX=2,NX_SHAPE_CONVEX=3,CapsuleCandidates=Candidates,IdentityIndex=Index,
  Contact=lambda:NS(point=Vec()),**{'std::numeric_limits<unsigned>::max':lambda:2**32-1})
 e['MapExactCapsuleToExpandedAABBTest']=lambda exact,mapped:call('MapExactCapsuleToExpandedAABBTest',exact=exact,mapped=mapped)
 for n in ['ConservativeCapsuleIntersectsAABB','ConservativeCapsuleIntersectsAABBReference']:
  e[n]=lambda mapped,bounds,n=n:call(n,mapped=mapped,bounds=bounds)
 status=v.run_body(v.body('OverlapCapsules'),e);return status,out,d,scene.commands,Counter(v.nativeReads)

batch_cases=0;reads_saved=0
for n in [2,4,8]:
 paths=[]
 for j in range(n):
  p=NS(to=NS(x=10,y=0,z=0),radius=1);setattr(p,'from',NS(x=0,y=0,z=0));paths.append(p)
 shapes=[]
 for k in range(60):
  b=Box();b.min=Vec(rng.uniform(-5,15),rng.uniform(-4,4),rng.uniform(-4,4));b.max=b.min+Vec(1,1,1)
  shapes.append(NS(box=b,identity=k//2,kind=99 if k%5==0 else 0,badGeometry=k%29==0))
 shapes+=['bad',None]
 for fail in [-1,3]:
  old=batch(paths,shapes,False,fail);new=batch(paths,shapes,True,fail)
  assert old[0]==new[0]==0 and old[3]==new[3]==1
  assert old[4]['getWorldBounds']==new[4]['getWorldBounds'] and new[4]['getType']==0
  reads_saved+=old[4]['getType']
  for a,b in zip(old[1],new[1]):assert {c.object.index for c in a.items}<={c.object.index for c in b.items}
  batch_cases+=1
 paths[-1].radius=float('nan');new=batch(paths,shapes,True);assert new[0]==0 and new[2].skippedInput==1;batch_cases+=1

# 原容量边界：520独立身份、重复形体、坏身份/几何不导致重查。
b=Box();b.min=Vec(0,0,0);b.max=Vec(1,1,1)
paths=[]
for j in range(2):
 p=NS(to=NS(x=10,y=0,z=0),radius=1);setattr(p,'from',NS(x=0,y=0,z=0));paths.append(p)
new=batch(paths,[NS(box=b,identity=i,kind=99,badGeometry=False) for i in range(520)],True)
assert new[0]==0 and new[3]==1 and all(x.count==520 for x in new[1]);batch_cases+=1

protected={}
for rel,names in [('IrisCombat.cpp',['DamageTarget','Collect','Flush','ResolveJobs','AdvanceEffects','Emit','Blast','PrepareShotBatch','PrepareBeamBatch']),('native/NativeMultiContact.cpp',['ReadObjectKey','SweepAll','ProjectileAll','RayBlocker','FinalizeSweep','BodyGeometry','SameRangedInput','ProbeRangedEmpty','ProbeRangedSpatial','BuildRangedSpatialGroups'])]:
 old=Program(norm(strip_observers((T/rel).read_text('utf8'))));new=Program(norm(strip_observers((R/rel).read_text('utf8'))))
 for name in names:assert old.tokens(old.body(name))==new.tokens(new.body(name)),name;protected[name]=True

# 所有C++单元语法，不调用编译器。旧非标准成员指针typedef沿已有验收方式隔离。
units=[]
for p in list(R.glob('*.cpp'))+list(R.glob('*.h'))+list((R/'native').glob('*.cpp'))+list((R/'native').glob('*.h')):
 text=norm(p.read_text('utf8'));text=re.sub(r'typedef Item\*\(RootObjectFactory::\* CreateMember\)\([^;]+;','typedef void* CreateMember;',text);Program(text);units.append(str(p.relative_to(R)))
for rel in ['distribution/IrisArsenal.ini','package/IrisArsenal/IrisArsenal.ini']:
 c=configparser.ConfigParser();c.read(R/rel,encoding='utf8');s=c['IrisArsenal'];assert s['EnableConservativeKernelReuse']=='1' and s['EnableConservativeProofAudit']=='0' and s['DamageFlushBudgetMs']=='2.5' and s['DamageFlushMaxHits']=='32'
for rel in ['tools/stage_package.py','tools/test_update_mod.py']:ast.parse((R/rel).read_text('utf8'))
from stage_package import validate_dll
try:validate_dll()
except RuntimeError as e:assert '095可证省工' in str(e);rejection=str(e)
else:raise AssertionError('不能将094旧DLL冒充095')
out=dict(actual_CPP_AST_kernel_cases=cases,padding_boundary_cases=1,kernel_superset_missing=0,extra_in_random=extras,
 conditional_cost_cases_by_parallel_axes=dict(per_parallel),deleted_operator_nodes=dict(deleted),actual_CPP_AST_batch_cases=batch_cases,
 saved_type_virtual_reads_in_batch_cases=reads_saved,protected_functions=protected,grammar_units=units,old_DLL_rejected=rejection,
 compiled=False,real_PhysX_timing=False,game_test=False,FPS_measured=False)
with args.out.open('x',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps(out,ensure_ascii=False,indent=2))
