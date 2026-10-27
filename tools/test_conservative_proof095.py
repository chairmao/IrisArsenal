"""095非编译对照验收：实际C++ AST＋SDK值替身；不代表PhysX耗时。"""
from pathlib import Path
from types import SimpleNamespace as NS
import sys,re,copy,json,math,argparse,tempfile
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from test_conservative094 import VM,Vec,Box,Contacts,Index
from test_query_boundary093 import strip_observers
from test_spatial_projectiles090 import norm
from read_conservative095 import analyze

COUNTS='batches timedBatches candidates typeReadsSaved parallelAxesSaved audits pairedCalls referenceShapeCalls comparedPaths approxUnique exactUnique extraUnique missingUnique invalidComparisons'.split()
TIMES='referenceKernelMs optimizedKernelMs exactShapeMs approximateStageMs auditMs'.split()
def sample():return NS(**dict.fromkeys(COUNTS+TIMES,0))
def key(n,serial=1):return NS(present=True,type=11,container=4,containerSerial=3,index=n,serial=serial)
def contact(k):return NS(object=k,point=Vec(),pointValid=False,fraction=0)

class AuditVM(VM):
 def __init__(self,s):super().__init__(s);self.cached={};self.clock=0;self.guards=0;self.shapeCalls=0
 def body(self,n):
  if n not in self.cached:self.cached[n]=super().body(n)
  return self.cached[n]
 def statement(self,n,e):
  if n.type=='type_definition':return
  if n.type=='declaration':
   text=self.txt(n)
   if text.startswith(('IrisDiagnostics::InterfaceScope','InterfaceScope')):return
   if text.startswith('Guard guard'):self.guards+=1;return
  return super().statement(n,e)
 def expr(self,n,e):
  if n.type=='call_expression':
   name=self.txt(n.child_by_field_name('function'));args=n.child_by_field_name('arguments').named_children
   if name=='ReadProofShapeType':
    shape=self.expr(args[0],e);self.assign(args[1],e,shape.kind);return not shape.badType
   if name=='CheckCapsuleGeometry':
    shape=self.expr(args[0],e);cap=self.expr(args[1],e);self.shapeCalls+=1
    self.assign(args[4],e,bool(shape.hitMask&(1<<int(cap.p0.x))));return not shape.badCheck
  return super().expr(n,e)

def main():
 native=(R/'native/NativeMultiContact.cpp').read_text('utf8');v=AuditVM(norm(strip_observers(native)))
 d=AuditVM(norm(strip_observers((R/'IrisDiagnostics.cpp').read_text('utf8'))))
 def now():v.clock+=.01;return v.clock
 env={'unsigned':int,'double':float,'float':float,'std::min':min,'std::max':max,'fabs':abs,'DBL_EPSILON':2**-52,
      'NxSphere':lambda:NS(center=Vec(),radius=0),'Contacts':Contacts,'IdentityIndex':Index,'Contact':lambda:NS(point=Vec()),
      'NX_SHAPE_SPHERE':0,'NX_SHAPE_CAPSULE':1,'NX_SHAPE_BOX':2,'NX_SHAPE_CONVEX':3,'IrisDiagnostics::Now':now,
      'std::numeric_limits<unsigned>::max':lambda:2**32-1}
 def cpp(name,**kw):return v.run_body(v.body(name),dict(env,**kw))
 env['ProofSameKey']=lambda a,b:cpp('ProofSameKey',a=a,b=b)
 for name in ('ConservativeCapsuleIntersectsAABB','ConservativeCapsuleIntersectsAABBReference'):
  env[name]=lambda mapped,bounds,n=name:cpp(n,mapped=mapped,bounds=bounds)
 for axis in range(6):
  a=key(9);b=copy.deepcopy(a);field=list(vars(b))[axis];setattr(b,field,not getattr(b,field) if axis==0 else getattr(b,field)+1)
  assert env['ProofSameKey'](a,a) and not env['ProofSameKey'](a,b)
 checks=0
 for count in (2,4,8):
  for bad in ('none','type','check','unsupported'):
   # 三个独立身份含同index不同serial，另有重复形体；正式结果预先独立拥有。
   box=Box();box.min=Vec(-20,-20,-20);box.max=Vec(20,20,20)
   items=[]
   for k in (key(1),key(1,2),key(1),key(2)):
    sh=NS(kind=0,hitMask=0x55,badType=False,badCheck=False)
    items.append(NS(shape=sh,key=k,bounds=box,typeBit=16,hitMask=0xff))
   if bad=='type':items[0].shape.badType=True
   if bad=='check':items[0].shape.badCheck=True
   if bad=='unsupported':items[0].shape.kind=99
   caps=[NS(p0=Vec(p,0,0),p1=Vec(p+1,0,0),radius=1) for p in range(count)]
   mapped=[NS(origin=[p,0,0],inverse=[1,0,0],radius=1,parallel=6) for p in range(count)]
   out=[Contacts() for _ in caps]
   for result in out:
    for k in (key(1),key(1,2),key(2),key(3)):result.Append(contact(k))
   snapshot=copy.deepcopy([[vars(x.object) for x in r.items] for r in out]);s=sample();before=v.shapeCalls
   cpp('AuditConservativeProof',capsules=caps,mapped=mapped,pathBounds=[box]*count,count=count,validPaths=(1<<count)-1,candidates=NS(count=len(items),At=lambda i:items[i]),results=out,sample=s)
   assert snapshot==[[vars(x.object) for x in r.items] for r in out]
   assert s.audits==1 and s.pairedCalls==count*len(items)*64 and s.referenceKernelMs>0 and s.optimizedKernelMs>0
   assert s.referenceShapeCalls==v.shapeCalls-before
   if bad=='none':
    expected=(count+1)//2*3
    assert s.invalidComparisons==0 and s.comparedPaths==count and s.exactUnique==expected and s.approxUnique==count*4
    assert s.extraUnique==s.approxUnique-s.exactUnique and s.missingUnique==0
   else:assert s.invalidComparisons==count and s.comparedPaths==s.approxUnique==s.exactUnique==0
   checks+=1
 # 关闭计数总门时不进统计锁；64位计数合并，进程/窗口独立累计。
 window=[sample(),sample()];x=sample();x.batches=1;x.candidates=2**33;x.auditMs=1.25
 for enabled in (False,True,True):
  d.run_body(d.body('RecordConservativeProof'),{'s':x,'proof095':window,'ConservativeQueryLoggingEnabled':lambda:enabled})
 assert d.guards==2 and all(w.candidates==2**34 and w.batches==2 and w.auditMs==2.5 for w in window)
 # 完整窗口、重复摘要、process累计、截断写入与精确零分母。
 with tempfile.TemporaryDirectory(prefix='iris095-reader-') as tmp:
  p=Path(tmp)/'fixture.log';prefix='2026-10-25 03:00:00.000 [IrisArsenal 0.4.46] '
  def row(i,scope='window',approx=12,exact=10):return prefix+f'audit_conservative_proof contract=IRIS_CONSERVATIVE_PROOF_095 id={i} scope={scope} batches=1 timed_batches=1 audits=1 approx_unique={approx} exact_unique={exact} extra_unique={approx-exact} missing_unique=0 reference_kernel_ms=2 optimized_kernel_ms=1 exact_shape_ms=4 approximate_stage_ms=3 audit_total_ms=8'
  p.write_text('\n'.join([row(1),row(1,'process',120,100),prefix+'audit_summary_end id=1',row(1),prefix+'audit_summary_end id=1',row(2),prefix+'audit_summary_end id=2',row(3)]),encoding='utf8')
  a=analyze(p);assert a['windows']==2 and a['incomplete_windows_ignored']==1 and a['approx_unique']==24 and a['approximate_to_exact_ratio']==1.2 and a['set_balance_valid']
  p.write_text(row(4,approx=1,exact=0)+'\n'+prefix+'audit_summary_end id=4',encoding='utf8');assert analyze(p)['approximate_to_exact_ratio'] is None
 # 测试语义不改变正式消费；计数门关闭不启动audit；顺序和所有权从实际源码核对。
 body=v.txt(v.body('OverlapCapsules'))
 assert body.index('out.diagnostic.uniqueBeforeFailure=out.count')<body.index('AuditConservativeProof(')
 assert 'const bool audit=proofLogging&&candidates.count&&conservativeProofAudit&&' in body
 assert 'if(proofLogging){' in body and 'sample.approximateStageMs=sample.exactShapeMs=0' in body
 return dict(actual_CPP_AST_audit_cases=checks,full_identity_fields=6,original_results_preserved=True,disabled_gate_lock_entries=0,Count_width_source='unsigned __int64',aggregation_over_32bit=True,reader_complete_window_tests=True,compiled=False,real_PhysX_or_QPC_test=False,game_test=False)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path);a=p.parse_args();r=main()
 if a.out:
  with a.out.open('x',encoding='utf8') as f:json.dump(r,f,ensure_ascii=False,indent=2)
 print(json.dumps(r,ensure_ascii=False,indent=2))
