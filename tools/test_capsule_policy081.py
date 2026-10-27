"""081非编译验证：实际C++条件AST、解析几何、动态身份索引/故障规格；不执行C++/PhysX。"""
from pathlib import Path
from types import SimpleNamespace as NS
import argparse,ast,configparser,hashlib,json,math,random,re
from test_performance080 import Program
from test_capsule_batch056 import exact,bounds,shape_bounds,overlaps,scheduling_cases
ROOT=Path(__file__).resolve().parents[1]
class Expressions(Program):
 def expr(self,n,e):
  if n.type=='unary_expression' and self.txt(n).lstrip().startswith('~'):return ~self.expr(n.named_children[-1],e)
  if n.type=='binary_expression':
   l=n.child_by_field_name('left');r=n.child_by_field_name('right');op=self.source[l.end_byte:r.start_byte].decode().strip()
   if op in ('&','|','%'):
    a,b=self.expr(l,e),self.expr(r,e)
    return {'&':lambda:a&b,'|':lambda:a|b,'%':lambda:a%b}[op]()
  return super().expr(n,e)
def digest(b):return hashlib.sha256(b).hexdigest()
def check_shadow(c):
 p=Expressions(c);node=next(n.child_by_field_name('value') for n in p.nodes('init_declarator') if p.txt(n).startswith('shadow='));cases=0
 for flag in (False,True):
  for warm in (0,7,8):
   for types in (0,1,2,3,8):
    for serial in (0,254,255,256,511):
     for complete in (False,True):
      e=dict(capsuleBatchShadowEnabled=flag,complete=complete,diagnostic=NS(shapeTests=int(bool(types)),shapeTypes=types),capsuleBatchWarm=warm,capsuleBatchVerifiedTypes=1,capsuleBatchSerial=serial)
      eligible=flag and complete and bool(types)
      increments=int(eligible and warm>=8 and not(types&~1))
      expected=eligible and (warm<8 or bool(types&~1) or (serial+1)%256==0)
      actual=p.expr(node,e);assert bool(actual)==bool(expected);assert e['capsuleBatchSerial']==serial+increments;cases+=1
 # 默认关闭连续10万批不触发旧查询或改变首次/类型/周期状态。
 e=dict(capsuleBatchShadowEnabled=False,complete=True,diagnostic=NS(shapeTests=8192,shapeTypes=15),capsuleBatchWarm=0,capsuleBatchVerifiedTypes=0,capsuleBatchSerial=255)
 for _ in range(100000):assert not p.expr(node,e)
 assert e['capsuleBatchSerial']==255
 return cases+100000
class Index:
 def __init__(self):self.keys=[];self.slots=None;self.capacity=512;self.probes=0;self.growth=0
 @staticmethod
 def hash(k):
  h=2166136261
  for v in k:h=((h^int(v))*16777619)&0xffffffff
  return h
 def insert(self,i):
  at=self.hash(self.keys[i])&(self.capacity-1)
  while self.slots[at] is not None:self.probes+=1;at=(at+1)&(self.capacity-1)
  self.slots[at]=i
 def add(self,key):
  if self.slots is None and len(self.keys)<8:
   if key in self.keys:return self.keys.index(key)
   self.keys.append(key);return len(self.keys)-1
  if self.slots is None or len(self.keys)>=self.capacity//2:
   if self.slots is not None:self.capacity*=2;self.growth+=1
   self.slots=[None]*self.capacity
   for i in range(len(self.keys)):self.insert(i)
  at=self.hash(key)&(self.capacity-1)
  while self.slots[at] is not None:
   if self.keys[self.slots[at]]==key:return self.slots[at]
   at=(at+1)&(self.capacity-1)
  self.keys.append(key);self.insert(len(self.keys)-1);return len(self.keys)-1
class Buffer:
 def __init__(self):self.values=[];self.capacity=256;self.allocations=0
 def append(self,v,fail=False):
  if len(self.values)==self.capacity:
   if fail:return False
   self.capacity*=2;self.allocations+=1
  self.values.append(v);return True
 def copy(self):
  r=Buffer()
  for v in self.values:assert r.append(v)
  return r
 def clear(self):self.values.clear()
def check_storage(native):
 # 实际源算法必须保留完整身份、按位FNV和动态半装载扩容；独立规格强制制造哈希冲突。
 for field in ('type','container','containerSerial','index','serial','present'):assert 'a.'+field+'==b.'+field in native
 assert 'h=2166136261U' in native and '16777619U' in native
 assert 'storage.resize(size_t(capacity)*2)' in native and 'std::numeric_limits<unsigned>::max()' in native
 cases=0
 for size in (0,1,7,8,255,256,257,511,512,513,1024,2049,4097):
  b=Buffer()
  for i in range(size):assert b.append(i)
  a=b.copy();b.clear();assert a.values==list(range(size)) and not b.values
  cap=b.capacity
  for i in range(size):assert b.append(-i)
  assert b.capacity==cap
  if size<=256:assert a.allocations==b.allocations==0
  cases+=1
 b=Buffer()
 for i in range(256):assert b.append(i)
 assert not b.append(256,True) and len(b.values)==256
 idx=Index();rng=random.Random(81056);keys=[(1,2,3,i*4096,7,True) for i in range(1500)]
 # 低12位相同，覆盖旧256哨兵、旧512表界和多轮扩容；乱序重复保持首次出现顺序。
 assert len({Index.hash(k)&4095 for k in keys})==1
 seq=keys+keys[::-1]+rng.choices(keys,k=1000);rng.shuffle(seq);expected=[];seen={}
 for k in seq:
  if k not in seen:seen[k]=len(expected);expected.append(k)
  assert idx.add(k)==seen[k]
 assert idx.keys==expected and len(idx.keys)==1500 and idx.capacity>=3000
 base=(1,2,3,4,5,True)
 for field in range(6):
  v=list(base);v[field]=0 if field==5 else v[field]+1
  assert tuple(v)!=base
  idx.add(tuple(v))
 idx.add(base);assert len(idx.keys)==1507
 # 相同目标的不同攻击段/施放仍分别提交，索引只在单条结果范围内。
 assert len({(cast,event,base) for cast,event in ((1,0),(1,1),(2,0))})==3
 return dict(buffer_boundaries=cases,collision_operations=len(seq)+7,unique_collision_keys=1500,table_capacity=idx.capacity,growth=idx.growth,heap_allocation_below_257=False)
def new_batch(paths,bodies,faults=None):
 boxes=[bounds(p,True) for p in paths];union=(tuple(min(b[0][i] for b in boxes) for i in range(3)),tuple(max(b[1][i] for b in boxes) for i in range(3)))
 result=[set() for _ in paths];tests=0;skipped=0
 for i,b in enumerate(bodies):
  if not overlaps(union,shape_bounds(b)):continue
  fault=(faults or {}).get(i)
  if fault in ('identity','bounds','nan','null'):skipped+=1;continue
  mask=0
  for p,path in enumerate(paths):
   if not overlaps(boxes[p],shape_bounds(b)):continue
   tests+=1
   if fault==('check',p):mask=0;skipped+=1;break
   if exact(path,b):mask|=1<<p
  for p in range(len(paths)):
   if mask&(1<<p) and b[-1] is not None:result[p].add(b[-1])
 return result,tests,skipped
def check_geometry(native):
 assert '++checks>1024' not in native and 'count==512' not in native and '==CONTACT_CAPACITY' not in native
 p=Program(native);body=p.txt(p.body('OverlapCapsules'))
 assert body.index('scene->overlapAABBShapes')<body.index('CheckCapsuleGeometry(')<body.index('out.Append(')
 assert 'candidate.hitMask=0;break;' in body and '++diagnostic.skippedGeometry;continue;' in body
 assert 'type!=NX_SHAPE_SPHERE&&type!=NX_SHAPE_CAPSULE&&type!=NX_SHAPE_BOX&&type!=NX_SHAPE_CONVEX' in body
 rng=random.Random(810284);cases=0
 for case in range(240):
  paths=[((rng.uniform(-30,30),0,0),(rng.uniform(-30,30),rng.uniform(-10,10),0),rng.choice((1,4.5,9))) for _ in range(2+case%7)]
  bodies=[]
  for i in range(30+case%130):
   a=(rng.uniform(-50,50),rng.uniform(-20,20),rng.uniform(-15,15));b=(a[0]+rng.uniform(-5,5),a[1]+rng.uniform(-5,5),a[2]+rng.uniform(-5,5))
   bodies.append(('capsule',a,b,rng.uniform(.1,2),i//2))
  actual,_,_=new_batch(paths,bodies)
  expected=[{b[-1] for b in bodies if exact(path,b)} for path in paths]
  assert actual==expected;cases+=1
 paths=[((0,0,0),(5,0,0),9)]*8
 dense=[('sphere',(0,0,0),(0,0,0),1,i) for i in range(4097)]
 actual,tests,skipped=new_batch(paths,dense)
 assert tests==32776 and all(len(s)==4097 for s in actual) and not skipped
 for faults in ({0:'identity',1:'bounds',2:'nan',3:'null',4:('check',4)}, {0:('check',7)}, {0:'identity',1:('check',0)}):
  actual,tests,skipped=new_batch(paths,dense[:700],faults)
  expected=set(range(700))-set(faults)
  assert all(s==expected for s in actual) and skipped==len(faults);cases+=1
 return dict(analytic_scenes=cases,dense_unique_targets=4097,dense_exact_checks=32776,bad_shape_whole_mask_discard=True,real_PhysX_executed=False)
def check_protected(before,c,n):
 oldc=(before/'IrisCombat.cpp').read_text('utf8');oldn=(before/'native/NativeMultiContact.cpp').read_text('utf8')
 pairs=[(c,oldc,['ResolveJobs','Flush','Collect','CanDamage','DamagePolicyReason','IgnoreRangedContact','Choose','PickRanged','Emit','Blast','End','Tick','WingCenter','Muzzle','DrawBeam','ElectroFrame','ProtectedMeleeMove','ProtectedRangedMove']), (n,oldn,['ProjectileAll','RayBlocker','BodyGeometry','Initialize','RuntimeVersionGate','RuntimeDecision','ReadObjectKey'])]
 count=0
 for new,old,names in pairs:
  a,b=Program(new),Program(old)
  for name in names:
   if name=='ResolveJobs':
    text=a.txt(a.body(name)).replace('(!hurts.empty()&&hurts.size()+j.victims.size()>2048)','hurts.size()+j.victims.size()>2048')
    aa=Program('void Test(){'+text+'}')
    # 去掉唯一授权的软水位门后，解析并比较整段词法，不能悄悄改变轮转/去重/医疗入队顺序。
    bb=Program('void Test(){'+b.txt(b.body(name))+'}')
    assert aa.tokens(aa.body('Test'))==bb.tokens(bb.body('Test')),name
   else:assert a.tokens(a.body(name))==b.tokens(b.body(name)),name
   count+=1
 return count
def main(before):
 c=(ROOT/'IrisCombat.cpp').read_text('utf8');n=(ROOT/'native/NativeMultiContact.cpp').read_text('utf8');h=(ROOT/'native/NativeMultiContact.h').read_text('utf8')
 # 仅当队列为空且单批>2048时放宽，所有普通规模与原门一致；大批不越过积压也不永久阻塞。
 queue_cases=0
 for queued in (0,1,31,1024,2047):
  for victims in (0,1,32,256,2047,2048,2049,4097,10000):
   old=queued+victims<=2048;new=queued==0 or queued+victims<=2048
   if victims<=2048:assert old==new
   if victims>2048:assert new==(queued==0)
   queue_cases+=1
 # 完整大批只入一次，之后既有32次硬上限/FIFO可最终清空，不能用“空队列例外”越过前批。
 queue=list(range(17));large=list(range(17,4114));submitted=False;done=[]
 while queue or not submitted:
  if not queue and not submitted:queue.extend(large);submitted=True
  done.extend(queue[:32]);del queue[:32]
 assert done==list(range(4114))
 out={'queue_admission_boundary_cases':queue_cases,'large_queue_FIFO_delivered':len(done),'shadow_actual_AST_cases':check_shadow(c),'storage_specification':check_storage(n),'geometry_specification':check_geometry(n),'protected_function_token_comparisons':check_protected(before,c,n),'scheduler_specification':scheduling_cases()}
 # 实际日志关闭门在QPC之前，调用日志在场景查询返回之后；仅复用既有摘要与安全互斥，不从回调写日志。
 p=Program(c);log=p.txt(p.body('LogCapsuleSkips'));assert log.index('DetailsEnabled()')<log.index('IrisDiagnostics::Now()')<log.index('Log(out.str())')
 batch=p.txt(p.body('TryCapsuleBatch'));assert batch.index('IrisNative::OverlapCapsules')<batch.index('LogCapsuleSkips(')
 assert 'capsuleBatchShadowEnabled=MoveSwitch(ini,"IrisArsenal","EnableCapsuleBatchShadow",false)' in c
 assert 'NxShape*' not in h and 'NxActor*' not in h
 # v100 SEH函数只借引用；NxSphere/NxBounds3在官方头内有显式析构，不能在__try函数本体构造。
 for name in ('ReadCapsuleGeometry','CheckCapsuleGeometry'):
  body=Program(n).txt(Program(n).body(name))
  assert not re.search(r'\b(?:NxSphere|NxBounds3|std::vector)\s+\w+',body),name
 assert 'const NxSphere& ball' in n
 # Query结果拥有自有连续存储，复制不别名；标量重置不释放工作区容量。
 for token in ('Contacts(const Contacts& other)','operator=(const Contacts& other)','bool Append(const Contact& value)'):assert token in h
 assert 'for(unsigned i=0;i<other.count;++i)items[i]=other.items[i]' in n and 'items=other.items' not in n
 for cfgpath in ('distribution/IrisArsenal.ini','package/IrisArsenal/IrisArsenal.ini'):
  old=configparser.ConfigParser();old.read(before/cfgpath,encoding='utf8');new=configparser.ConfigParser();new.read(ROOT/cfgpath,encoding='utf8')
  assert new.getint('IrisArsenal','EnableCapsuleBatchShadow')==0
  new.remove_option('IrisArsenal','EnableCapsuleBatchShadow');assert {k:dict(old[k]) for k in old.sections()}=={k:dict(new[k]) for k in new.sections()}
 dh=(ROOT/'IrisDiagnostics.h').read_text('utf8');dc=(ROOT/'IrisDiagnostics.cpp').read_text('utf8');oh=(before/'IrisDiagnostics.h').read_text('utf8')
 for enum,array,count in [('Kind','names','KIND_COUNT'),('Counter','counters','COUNTER_COUNT')]:
  def members(x):return [a.strip() for a in re.search(r'enum '+enum+r'\s*\{([^}]+)\}',x).group(1).split(',')][:-1]
  a,b=members(oh),members(dh);assert b[:len(a)]==a
  labels=re.findall(r'"([^"]+)"',re.search(r'\b'+array+r'\['+count+r'\]\s*=\{([^}]+)\}',dc).group(1));assert len(labels)==len(b)
 # 对所有翻译单元/接口做非编译语法解析；MSVC属性先删除，SEH保留交给语法器解析。
 syntax=[]
 for file in list(ROOT.glob('*.cpp'))+list(ROOT.glob('*.h'))+list((ROOT/'native').glob('*.cpp'))+list((ROOT/'native').glob('*.h')):
  text=file.read_text('utf-8-sig');text=re.sub(r'__declspec\((?:[^()]|\([^()]*\))*\)','',text);text=re.sub(r'\b__fastcall\b','',text)
  assert not Program(text).tree.root_node.has_error,str(file);syntax.append(str(file.relative_to(ROOT)))
 ast.parse((ROOT/'tools/stage_package.py').read_text('utf-8-sig'))
 stage=(ROOT/'tools/stage_package.py').read_text('utf8');assert "CAPSULE_POLICY_CONTRACT='IRIS_CAPSULE_POLICY_081'" in stage and 'if CAPSULE_POLICY_CONTRACT.encode' in stage
 out.update(syntax_checked=syntax,exception_log_after_query=True,logging_disabled_before_clock=True,SEH_no_destructible_locals=True,config_old_values_unchanged=True,diagnostic_enum_old_indexes_preserved=True,compiled=False,game_or_thread_tested=False,FPS_measured=False,white_list='unchanged pending real type support and performance evidence')
 return out
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--before',type=Path,required=True);a.add_argument('--out',type=Path,required=True);args=a.parse_args()
 result=main(args.before)
 with args.out.open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
 print(json.dumps(result,ensure_ascii=False,indent=2))
