"""091非编译验收：实际函数AST、调用链token及抽样关门；不模拟FPS或实际引擎线程。"""
from pathlib import Path
from types import SimpleNamespace as NS
import argparse,ast,configparser,itertools,json,math,random,re,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from test_native_profile084 import Eval,definitions,forwarders
from test_performance080 import Program,Returned
from test_medical_gate083 import replay
class VM(Eval):
 def expr(self,n,e):
  if n.type=='this':return e['this']
  if n.type=='initializer_list':return [self.expr(x,e) for x in n.named_children]
  if n.type=='pointer_expression' and self.txt(n).startswith('*'):return self.expr(n.named_children[-1],e)
  if n.type=='call_expression' and self.txt(n.child_by_field_name('function')).startswith('static_cast<'):
   return self.expr(n.child_by_field_name('arguments').named_children[0],e)
  if n.type=='primitive_type':return {'unsigned':lambda x:int(x)&0xffffffff,'float':float}[self.txt(n)]
  if n.type=='assignment_expression':
   l=n.child_by_field_name('left')
   if self.txt(l) in ('hit','previous','hit->top'):
    v=self.expr(n.child_by_field_name('right'),e);self.assign(l,e,v);return v
  return super().expr(n,e)
 def statement(self,n,e):
  if n.type=='try_statement':
   return self.statement(next(x for x in n.named_children if x.type=='compound_statement'),e)
  return super().statement(n,e)
 def run(self,body,e):
  try:self.statement(body,e)
  except Returned as r:return r.value

def text(p):return p.read_text('utf-8-sig')
def normal(s):return re.sub(r'__declspec\((?:[^()]|\([^()]*\))*\)','',s)
def clean(s,old):
 s=re.sub(r'IrisDiagnostics::WorkTrace workTrace\(IrisDiagnostics::WORK_(?:COMBAT|MEDICAL)\);','',s)
 s=re.sub(r'workTrace\.Mark\(IrisDiagnostics::WORK_\w+\);','',s)
 s=s.replace('a.lengths[j]=AnimationLength(c,j);','a.lengths[j]=Loaded(c,j)?c->animation->getAnimationState(moves[j].animation)->getLength():0;')
 # 正式实现已删除无调用的Loaded包装；旧版对照仍需该定义，仅在本次回放字符串中恢复。
 # 必须取自明确给定的历史源码，保留旧断言/逐函数比较，不向正式C++添加替身或跳过功能差异。
 q=Program(old);b=q.body('Loaded')
 if not re.search(r'\bbool\s+Loaded\s*\(',s):
  definition=next(n for n in q.nodes('function_definition') if n.child_by_field_name('body')==b)
  s+='\n'+q.txt(definition)+'\n'
 p=Program(s);a=p.body('Loaded')
 return (p.source[:a.start_byte]+q.source[b.start_byte:b.end_byte]+p.source[a.end_byte:]).decode()
def equivalent_calls(before,c):
 old=text(before/'IrisCombat.cpp');a,b=Program(old),Program(clean(c,old));count=0
 for n in a.nodes('function_definition'):
  body=n.child_by_field_name('body');header=a.source[n.start_byte:body.start_byte].decode()
  found=[m.child_by_field_name('body') for m in b.nodes('function_definition') if b.source[m.start_byte:m.child_by_field_name('body').start_byte].decode()==header]
  assert len(found)==1,header
  assert a.tokens(body)==b.tokens(found[0]),header;count+=1
 return count
def length_cases(c,old):
 p,q=VM(c),VM(old);new=definitions(p,'AnimationLength');prior=definitions(q,'Loaded');cases=0;saved=0

 for exists,anim,present,has_state,length in itertools.product([False,True],[False,True],[False,True],[False,True],[0.,-1.,2.5,float('nan'),float('inf')]):
  def setup():
   trace=[]
   class State:
    def getLength(self):trace.append('length');return length
   state=State() if has_state else None
   class Animation:
    def hasAnimation(self,key):trace.append('has');return present
    def getAnimationState(self,key):trace.append('state');return state
   character=NS(animation=Animation() if anim else None) if exists else None
   return dict(c=character,i=0,moves=[NS(animation='a')],Finite=math.isfinite),trace
  e,nt=setup();v=p.run(new,e);e2,ot=setup();ok=q.run(prior,e2)
  old_length=e2['c'].animation.getAnimationState('a').getLength() if ok else 0
  assert v==old_length,(exists,anim,present,has_state,length,v,old_length)
  assert len(nt)<=len(ot);saved+=len(ot)-len(nt);cases+=1
 return dict(actual_AST_cases=cases,total_getter_calls_saved_in_cases=saved,no_cross_call_cache=True)
def work_cases(d,h):
 p=VM(normal(d));ctor=definitions(p,'WorkTrace');mark=definitions(p,'Mark');dtor=definitions(p,'WorkTrace',True)
 enum=re.search(r'enum WorkPart \{([^}]+)\}',h)[1];parts=[x.strip() for x in enum.split(',')];n=parts.index('WORK_PART_COUNT')
 cases=0;disabled=0;sampled=0
 class Stat:
  def __init__(self):self.values=[]
  def Sample(self,x):self.values.append(x)
  def Frame(self,x):pass
 def stats():return NS(total=Stat(),parts=[Stat() for _ in range(n)],visits=[0]*n,exceptions=0)
 for own,parent,every in itertools.product([False,True],[False,True],[1,2,32,65536]):
  sequences=[0,0];rows=[stats(),stats()];rows2=[stats(),stats()]
  for k in range(65):
   touched=[];clock=[1000.]
   def now():touched.append('clock');clock[0]+=.125;return clock[0]
   def serial(ptr):touched.append('atomic');domain=0;sequences[domain]+=1;return sequences[domain]
   e=dict(domain=0,active=False,part=0,begin=0.,last=0.,elapsed=[None]*n,visits=[None]*n,workTraceEnabled=own,unsigned=lambda x:int(x)&0xffffffff,
      DetailsEnabled=lambda:parent,workTraceEvery=every,workTraceSequence=sequences,
      InterlockedIncrement=serial,Now=now,GetLastError=lambda:71,SetLastError=lambda v:None,_finite=math.isfinite,
      WORK_SETUP=0,WORK_PART_COUNT=n,value=0,workRun=rows,workWindow=rows2,
      **{'std::uncaught_exception':lambda:False})
   p.run(ctor,e);active=e['active']
   for v in [1,3,3,9,13,16,19]:e['value']=v;p.run(mark,e)
   p.run(dtor,e)
   expected=own and parent and k%every==0
   assert active==expected,(own,parent,every,k)
   if not own or not parent:
    assert not touched;disabled+=1
   elif not active:assert touched==['atomic']
   else:
    assert math.isclose(sum(e['elapsed']),e['last']+.125-e['begin'])
    sampled+=1
   cases+=1
 # QPC后退只忽略该标记，不能污染总和；析构/早退分段始终闭合。
 e['active']=True;e['last']=10;e['part']=0;e['value']=2;e['elapsed']=[0.]*n;e['Now']=lambda:9
 p.run(mark,e);assert e['elapsed']==[0.]*n and e['part']==0
 return dict(actual_ctor_mark_destructor_AST_calls=cases,disabled_zero_clock_atomic_lock_cases=disabled,sampled_scopes=sampled,
             no_unsampled_clock=True,phase_sum_equals_sample_wall=True,fixed_parts=n,clock_rollback_ignored=True)
def gap_cases(n):
 p=VM(n);ctor=definitions(p,'PartScope');dtor=definitions(p,'PartScope',True);rng=random.Random(91);cases=0
 for active,profile in itertools.product([False,True],repeat=2):
  for pattern in range(120):
   begin=100.;hit=NS(top=None,gapActive=profile,gapCursor=begin,gaps=[0.]*5,calls=[0]*4,inclusive=[0.]*4,exclusive=[0.]*4)
   clock=[begin]
   # 顶层顺序允许反复/缺失；嵌套父子可同类型，间隙只在top层生成。
   for j in range(pattern%7):
    clock[0]+=.01+rng.random();part=rng.randrange(4);start=clock[0]
    env=dict(hit=None,previous=None,part=part,begin=0.,children=0.,Enabled=lambda:active,this=NS(children=0.),
      GetLastError=lambda:123,SetLastError=lambda v:None,hitTLS=5,ReadTLS=lambda _:hit,
      _finite=math.isfinite,**{'IrisDiagnostics::Now':lambda:clock[0],'std::max':max})
    p.run(ctor,env);clock[0]+=.01
    if active and j%2==0:
     child=dict(env,hit=None,previous=None,part=(part+1)%4,begin=0.,children=0.)
     # top指针是当前scope的this；解释器用namespace显式绑定，保持父children更新。
     parent=NS(children=0.)
     hit.top=parent;p.run(ctor,child);clock[0]+=.03;p.run(dtor,child)
     env['children']=parent.children;hit.top=None
    clock[0]+=.04;p.run(dtor,env);assert hit.top is None
   clock[0]+=.02
   if active and profile:
    hit.gaps[4]+=clock[0]-hit.gapCursor
    assert math.isclose(sum(hit.gaps)+sum(hit.exclusive),clock[0]-begin,abs_tol=1e-9)
   elif not profile:assert hit.gaps==[0.]*5
   cases+=1
 return dict(actual_PartScope_AST_scenarios=cases,top_level_gaps_plus_exclusive_equal_root=True,nested_duplicate_parts=True)
def native_root_sampling(n):
 p=VM(n);ctor=definitions(p,'Hit');cases=0
 for enabled,parent_present,write_ok,gap_option,every in itertools.product([False,True],[False,True],[False,True],[False,True],[1,2,32]):
  sequence=[0]
  for index in range(34):
   operations=[];parent=NS(nested=0) if parent_present else None
   def serial(_):sequence[0]+=1;operations.append('gap_atomic');return sequence[0]
   e=dict(active=False,gapActive=False,gapCursor=0.,begin=0.,nested=0,top=None,inclusive=[None]*4,
     exclusive=[None]*4,calls=[None]*4,gaps=[None]*5,PART_COUNT=4,Enabled=lambda:enabled,
     GetLastError=lambda:123,SetLastError=lambda _:None,ReadTLS=lambda _:parent,hitTLS=0,
     Generation=lambda:7,WriteTLS=lambda slot,who:write_ok,
     gapOption=gap_option,gapSequence=0,gapEvery=every,unsigned=int,InterlockedIncrement=serial,
     this=object(),**{'IrisDiagnostics::Now':lambda:operations.append('existing_clock') or 100.})
   p.run(ctor,e)
   expect_active=enabled and not parent_present and write_ok
   expect_gap=expect_active and gap_option and index%every==0
   assert e['active']==expect_active and e['gapActive']==expect_gap
   assert operations.count('existing_clock')==int(expect_active)
   assert operations.count('gap_atomic')==int(expect_active and gap_option)
   if expect_gap:assert e['gaps']==[0.]*5 and e['gapCursor']==100.
   if enabled and parent_present:assert parent.nested==1
   cases+=1
 return dict(actual_Hit_ctor_AST_cases=cases,disabled_or_nested_no_extra_clock=True,reuses_single_existing_root_clock=True)

def main(before,out):
 c=text(ROOT/'IrisCombat.cpp');d=text(ROOT/'IrisDiagnostics.cpp');h=text(ROOT/'IrisDiagnostics.h');n=text(ROOT/'IrisNativeAudit.cpp')
 result=dict(original_combat_functions_preserved=equivalent_calls(before,c),
             length_lookup=length_cases(c,text(before/'IrisCombat.cpp')),
             work_trace=work_cases(d,h),native_gaps=gap_cases(n),native_sampling=native_root_sampling(n),original_forwarding=forwarders(VM(n)))
 # 新native追踪只复用原时钟；诊断关闭没有新增引擎调用或Hook。既有非诊断单元逐字保持。
 oldn=text(before/'IrisNativeAudit.cpp');assert oldn.count('IrisDiagnostics::Now()')==n.count('IrisDiagnostics::Now()')
 assert oldn.count('KenshiLib::AddHook(')==n.count('KenshiLib::AddHook(')==2
 for f in ['IrisArsenal.cpp','IrisRanged.cpp','IrisWoundAudit.cpp','IrisWoundAudit.h','native/NativeMultiContact.cpp','native/NativeMultiContact.h']:
  assert (before/f).read_bytes()==(ROOT/f).read_bytes(),f
 result['medical_FIFO_specs']=replay(clean(c,text(before/'IrisCombat.cpp')))
 syntax=[]
 for f in list(ROOT.glob('*.cpp'))+list(ROOT.glob('*.h'))+list((ROOT/'native').glob('*.cpp'))+list((ROOT/'native').glob('*.h')):
  s=normal(text(f));s=re.sub(r'typedef Item\*\(RootObjectFactory::\* CreateMember\)\([^;]+;','typedef void* CreateMember;',s);Program(s);syntax.append(str(f.relative_to(ROOT)))
 result['grammar_units']=syntax
 for f in ['distribution/IrisArsenal.ini','package/IrisArsenal/IrisArsenal.ini']:
  ini=configparser.ConfigParser();ini.read(ROOT/f,encoding='utf8');section=ini['IrisArsenal']
  assert all(section[k]=='1' for k in ['EnableWorkPhaseProfiling','EnableNativeGapProfiling'])
  assert section['WorkPhaseSampleEvery']=='32'
 for f in ['tools/stage_package.py','tools/test_update_mod.py',__file__]:ast.parse(text(Path(f) if f==__file__ else ROOT/f))
 from stage_package import validate_dll
 try:validate_dll()
 except RuntimeError as e:assert '091抽样阶段追踪' in str(e);result['actual_old_DLL_refused']=str(e)
 else:raise AssertionError('旧DLL不能冒充091')
 result.update(compiled=False,engine_or_real_threads_tested=False,FPS_measured=False)
 out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
 q=argparse.ArgumentParser();q.add_argument('--before',type=Path,required=True);q.add_argument('--out',type=Path,required=True);a=q.parse_args();main(a.before,a.out)
