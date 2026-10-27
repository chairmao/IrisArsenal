"""087非编译验证：解释实际C++ AST、对照原命中集合与纯值计算；不模拟PhysX或线程。"""
from pathlib import Path
from types import SimpleNamespace as NS
import argparse,ast,configparser,copy,hashlib,itertools,json,math,random,re,struct,sys
ROOT=Path(__file__).resolve().parents[1]
cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--before',type=Path,required=True);cli.add_argument('--out',type=Path,required=True);args=cli.parse_args()
BEFORE=args.before;TASK=args.out.parent
sys.path.insert(0,str(ROOT/'tools'))
from test_native_profile084 import Eval,definitions
from test_performance080 import Program,Returned
from test_medical_gate083 import replay
def read(p):return p.read_text('utf-8-sig')
def tokens(text):p=Program(text);return p.tokens(p.tree.root_node)
def body(p,name):return p.body(name)
def method(p,cls,name):
 c=next(n for n in p.nodes('struct_specifier') if p.txt(n.child_by_field_name('name'))==cls)
 return next(n.child_by_field_name('body') for n in p.nodes('function_definition') if c.start_byte<n.start_byte<n.end_byte<c.end_byte and re.search(r'\b'+name+r'\s*\(',p.source[n.start_byte:n.child_by_field_name('body').start_byte].decode()))
class VM(Eval):
 def expr(self,n,e):
  if n.type=='number_literal' and self.txt(n).lower().startswith('0x'):return int(re.sub('[uUlL]+$','',self.txt(n)),16)
  if n.type=='assignment_expression':
   l=n.child_by_field_name('left');r=n.child_by_field_name('right');op=self.source[l.end_byte:r.start_byte].decode().strip();v=self.expr(r,e)
   if op!='=':
    a=self.expr(l,e);v={'+=':lambda:a+v,'*=':lambda:a*v,'^=':lambda:a^v,'|=':lambda:a|v}[op]()
   if l.type=='identifier' and self.txt(l)=='h':v&=0xffffffff
   self.assign(l,e,copy.deepcopy(v));return v
  if n.type=='binary_expression':
   l=n.child_by_field_name('left');r=n.child_by_field_name('right');op=self.source[l.end_byte:r.start_byte].decode().strip()
   if op in ('&','^','>>','<<'):
    a,b=self.expr(l,e),self.expr(r,e);return {'&':lambda:a&b,'^':lambda:a^b,'>>':lambda:a>>b,'<<':lambda:a<<b}[op]()
  if n.type=='call_expression' and self.txt(n.child_by_field_name('function'))=='unsigned':return int(self.expr(n.child_by_field_name('arguments').named_children[0],e))&0xffffffff
  return super().expr(n,e)
 def statement(self,n,e):
  if n.type=='else_clause':return self.statement(n.named_children[-1],e)
  if n.type=='continue_statement':raise Continue()
  if n.type=='declaration' and self.txt(n).startswith('IrisDiagnostics::Scope '):return
  if n.type=='for_statement':
   init=n.child_by_field_name('initializer');cond=n.child_by_field_name('condition');upd=n.child_by_field_name('update')
   if init:self.statement(init,e)
   guard=0
   while cond is None or self.expr(cond,e):
    try:self.statement(n.child_by_field_name('body'),e)
    except Continue:pass
    if upd:self.expr(upd,e)
    guard+=1;assert guard<100000
   return
  return super().statement(n,e)
class Continue(Exception):pass
def execute(p,n,e):
 try:p.statement(n,e)
 except Returned as x:return x.value
 return None
def key(vals):return NS(**dict(zip(('type','container','containerSerial','index','serial','present'),vals)))
def tup(k):return tuple(getattr(k,n) for n in ('type','container','containerSerial','index','serial','present'))
class Handle:
 def __init__(self,k,gets):self.key=tup(k);self.gets=gets
 def getCharacter(self):self.gets.append(self.key);return self.key
 def __hash__(self):return hash(self.key)
 def __eq__(self,o):return isinstance(o,Handle) and self.key==o.key
class Victims(set):
 def find(self,h):return h if h in self else None
 def end(self):return None
 def insert(self,h):self.add(h)

old=VM(read(BEFORE/'IrisCombat.cpp'));new=VM(read(ROOT/'IrisCombat.cpp'))
equal=body(new,'SameContactIdentity');hashbody=body(new,'ContactMemoSlot')
def same(a,b):return execute(new,equal,dict(a=a,b=b))
def slot(k):return execute(new,hashbody,dict(key=k))
def run_memo(p,seq,forced=None):
 gets=[];calls=[];states=dict(occupied=0,previous=None,valid=False,ignored=False,checks=0,reuses=0,collisions=0,slots=[NS(key=None,ignored=False) for _ in range(16)])
 def policy(c,v):calls.append(v);return v[-2]%3!=0
 e=dict(states,caster='caster',SameContactIdentity=same,ContactMemoSlot=slot if forced is None else lambda k:forced,IgnoreRangedContact=policy)
 n=method(p,'RangedContactMemo','Ignore');result=[]
 for k in seq:
  e.update(key=k,identity=Handle(k,gets));result.append(execute(p,n,e))
 return result,len(gets),len(calls),e
random.seed(87001);streams=[[],[key((1,2,3,4,5,True))]*12]
pool=[key((1,i%3,100+i%4,i,1000+i,True)) for i in range(90)]
for length in (1,8,17,64,257,700):
 for _ in range(12):streams.append([random.choice(pool) for _ in range(length)])
# 同下标但每个其余身份字段不同；既测真实哈希冲突，也强制所有完整身份落同一槽。
seed=(1,2,3,4,5,True)
variants=[key(seed)]
for field in range(6):
 x=list(seed);x[field]=(not x[field]) if field==5 else x[field]+1;variants.append(key(x))
streams+=[variants*30,list(reversed(variants))*30]
memo_calls=0
for seq in streams:
 a=run_memo(old,seq)
 for forced in (None,0,15):
  b=run_memo(new,seq,forced);assert a[0]==b[0];assert b[1]<=a[1];memo_calls+=len(seq)
  assert b[3]['checks']+b[3]['reuses']==len(seq)
for a,b in itertools.product(variants,repeat=2):assert same(a,b)==(tup(a)==tup(b))
assert {slot(k) for k in pool}==set(range(16))
repeat=[pool[1],pool[2]]*100
old_repeat=run_memo(old,repeat);new_repeat=run_memo(new,repeat);assert new_repeat[1]<old_repeat[1]

def collect_run(p,seq,accepted,eligible,audit):
 gets=[];checks=[];counts={}
 j=NS(caster=NS(getCharacter=lambda:'caster'),move=3,victims=Victims(Handle(k,gets) for k in accepted))
 def policy(c,v,m):checks.append(v);return eligible.get(v,False)
 e=dict(j=j,hits=NS(count=len(seq),items=[NS(object=k) for k in seq]),Handle=lambda k:Handle(k,gets),DamageTarget=policy)
 e.update({'IrisDiagnostics::CollisionProfileEnabled':lambda:audit,'IrisDiagnostics::Add':lambda k,n:counts.__setitem__(k,counts.get(k,0)+n)})
 for c in ['COLLECT_CONTACTS','COLLECT_DUPLICATES','COLLECT_CHECKS','COLLECT_INSERTS']:e['IrisDiagnostics::'+c]=c
 execute(p,body(p,'Collect'),e)
 return {h.key for h in j.victims},len(gets),len(checks),counts
collect_cases=0
for length in (0,1,8,17,256,601):
 for mode in range(8):
  seq=[random.choice(pool[:30]) for _ in range(length)];accepted=pool[:mode];eligible={tup(k):random.choice([True,False]) for k in pool}
  a=collect_run(old,seq,accepted,eligible,False)
  for audit in [False,True]:
   b=collect_run(new,seq,accepted,eligible,audit);assert a[0]==b[0];assert b[1]<=a[1];assert b[2]<=a[2]
   if audit:assert b[3].get('COLLECT_CONTACTS',0)==b[3].get('COLLECT_DUPLICATES',0)+b[3].get('COLLECT_CHECKS',0)
   else:assert not b[3]
   collect_cases+=1

# 实际float采样表达式AST；每步float运算取float32，不把Python double近似称C++实测。
f32=lambda x:struct.unpack('f',struct.pack('f',x))[0]
class FloatVM(VM):
 def expr(self,n,e):
  v=super().expr(n,e)
  if n.type in ('binary_expression','number_literal') and isinstance(v,float):return f32(v)
  return v
fp=FloatVM(read(ROOT/'IrisCombat.cpp'));op=FloatVM(read(BEFORE/'IrisCombat.cpp'))
draw=method(fp,'Visual','Draw');odraw=method(op,'Visual','Draw')
oldpos=next(n for n in op.nodes('declaration') if odraw.start_byte<n.start_byte<n.end_byte<odraw.end_byte and op.txt(n).startswith('float x=std::max'))
# 旧声明一行里x、lo/hi、u/v是三个declaration，逐个执行取到u为止。
oldgroup=[n for n in op.nodes('declaration') if oldpos.start_byte<=n.start_byte<oldpos.start_byte+260 and n.end_byte<odraw.end_byte][:3]
init=next(n for n in fp.nodes('declaration') if draw.start_byte<n.start_byte<n.end_byte<draw.end_byte and fp.txt(n).startswith('float sampleAge='))
calc=next(n for n in fp.nodes('if_statement') if draw.start_byte<n.start_byte<n.end_byte<draw.end_byte and fp.txt(n).startswith('if(updateParameters&&asset.samples)'))
common_unsigned=next(n for n in fp.nodes('declaration') if draw.start_byte<n.start_byte<n.end_byte<draw.end_byte and fp.txt(n).startswith('unsigned sampleLo='))
newpos=next(n for n in fp.nodes('declaration') if draw.start_byte<n.start_byte<n.end_byte<draw.end_byte and fp.txt(n).startswith('unsigned lo=sampleLo'))
newu=next(n for n in fp.nodes('declaration') if newpos.end_byte<=n.start_byte<newpos.end_byte+8 and fp.txt(n).startswith('float u=sampleU'))
fallback=next(n for n in fp.nodes('if_statement') if draw.start_byte<n.start_byte<n.end_byte<draw.end_byte and fp.txt(n).startswith('if(layerAge!=sampleAge)'))
float_cases=0
for samples,duration,age,factor in itertools.product([1,2,17,240],[.001,.52,1.1,8.17],[-.1,0,.001,.2,.52,1.,10.],[1.,.5,2.]):
 asset=NS(samples=samples,duration=f32(duration));age=f32(age);layerAge=f32(age*factor)
 common=dict(asset=asset,age=age,key='asset',updateParameters=True,VisualLayerAge=lambda k,i,a:a,**{'std::max':max,'std::min':min})
 execute(fp,init,common);execute(fp,common_unsigned,common);execute(fp,calc,common);e=dict(common,layerAge=layerAge)
 execute(fp,newpos,e);execute(fp,newu,e);execute(fp,fallback,e)
 oldenv=dict(common,layerAge=layerAge)
 for n in oldgroup:execute(op,n,oldenv)
 assert (e['lo'],e['hi'],struct.pack('f',e['u']))==(oldenv['lo'],oldenv['hi'],struct.pack('f',oldenv['u'])),(samples,duration,age,factor,e,oldenv)
 float_cases+=1

# 除明确列出的消费者/诊断段，原行为函数逐token完全相同；尤其原生资格与最终医疗整段保留。
def functions(p):
 result={}
 for n in p.nodes('function_definition'):
  b=n.child_by_field_name('body');head=p.source[n.start_byte:b.start_byte].decode();result[head]=p.tokens(b)
 return result
changes={'Ignore','Collect','Draw','Swing','AdvanceEffects','ResolveJobs','ShowParts','UpdateTrail'}
a,b=functions(old),functions(new);protected=[]
for head,ts in a.items():
 name=re.search(r'(\w+)\s*\([^()]*\)\s*$',head)
 if (name and name[1] in changes) or head.startswith('RangedContactMemo('):continue
 assert head in b and b[head]==ts,head;protected.append(head)
# 原生查询/回调除新观察不变；删除观察AST节点后，控制/调用token顺序保留。
def unobserve(p,n):
 cuts=[]
 def visit(node):
  text=p.txt(node)
  if node.type=='declaration' and text.startswith('IrisDiagnostics::Scope '):cuts.append((node.start_byte,node.end_byte));return
  if node.type=='if_statement' and text.startswith('if(IrisDiagnostics::CollisionProfileEnabled())'):cuts.append((node.start_byte,node.end_byte));return
  for c in node.named_children:visit(c)
 visit(n);data=p.source[n.start_byte:n.end_byte]
 for a,b in sorted(cuts,reverse=True):data=data[:a-n.start_byte]+data[b-n.start_byte:]
 return [x for x in tokens('void X()'+data.decode()) if x not in ('{','}')]
nat_old=Program(read(BEFORE/'native/NativeMultiContact.cpp'));nat_new=Program(read(ROOT/'native/NativeMultiContact.cpp'))
for name in ['RayBlocker','SweepAll','OverlapCapsules']:
 assert unobserve(nat_old,body(nat_old,name))==unobserve(nat_new,body(nat_new,name)),name
assert unobserve(old,body(old,'ResolveJobs'))==unobserve(new,body(new,'ResolveJobs'))
for name in ['ReadObjectKey','ProjectileAll','OverlapSphere','OverlapCapsule','CylinderAll']:
 assert nat_old.tokens(body(nat_old,name))==nat_new.tokens(body(nat_new,name)),name
for name in ['IrisArsenal.cpp','IrisNativeAudit.cpp','IrisWoundAudit.cpp','IrisRanged.cpp','native/NativeMultiContact.h']:
 before=BEFORE/name
 if before.exists():assert before.read_bytes()==(ROOT/name).read_bytes(),name
fifo_replay=replay(read(ROOT/'IrisCombat.cpp'))

# 枚举只追加；四个开关任一关闭，新阶段和新计数都必须短路。
hd=read(ROOT/'IrisDiagnostics.h');di=Program(re.sub(r'__declspec\((?:[^()]|\([^()]*\))*\)','',read(ROOT/'IrisDiagnostics.cpp')))
oldhd=read(BEFORE/'IrisDiagnostics.h')
for enum in ['Kind','Counter']:
 extract=lambda s:re.findall(r'\b[A-Z][A-Z_]+\b',re.search(r'enum '+enum+r' \{([^}]+)\}',s).group(1))[:-1]
 assert extract(hd)[:len(extract(oldhd))]==extract(oldhd)
gate_cases=0
for enable,perf,detail,local in itertools.product([False,True],repeat=4):
 e=dict(enabled=enable,performance=perf,details=detail,collisionProfile=local)
 e['DetailsEnabled']=lambda:enable and perf and detail
 value=execute(di,body(di,'CollisionProfileEnabled'),e);assert value==(enable and perf and detail and local);gate_cases+=1
for name in ['distribution/IrisArsenal.ini','package/IrisArsenal/IrisArsenal.ini']:
 before=configparser.ConfigParser();after=configparser.ConfigParser();before.read_string(read(BEFORE/name));after.read_string(read(ROOT/name))
 assert after['IrisArsenal']['EnableCollisionDetailProfiling']=='1';after.remove_option('IrisArsenal','EnableCollisionDetailProfiling');assert dict(before)==dict(after)
stage=read(ROOT/'tools/stage_package.py');ast.parse(stage);assert "CONTACT_WORK_CONTRACT='IRIS_CONTACT_WORK_087'" in stage and 'if CONTACT_WORK_CONTRACT.encode' in stage
pkg=json.loads(read(ROOT/'package/IrisArsenal/IrisPackage.json'));assert pkg['ready'] is False and pkg['pending_source_version']=='0.4.38' and pkg['version']=='0.4.37'
assert hashlib.sha256((ROOT/'package/IrisArsenal/IrisArsenal.ini').read_bytes()).hexdigest()==pkg['files']['IrisArsenal.ini']
result={'memo_streams':len(streams),'memo_AST_lookups':memo_calls,'full_identity_pairs':len(variants)**2,'forced_collision_slots':[0,15],'alternating_old_policy_checks':old_repeat[1],'alternating_new_policy_checks':new_repeat[1],'collect_set_cases':collect_cases,'float32_sample_position_cases':float_cases,'protected_functions':len(protected),'config_gate_cases':gate_cases,'native_query_signature_and_consumption_unchanged':True,'medical_FIFO_and_safety_unchanged':True,'FIFO_reentry_specs':fifo_replay,'compiled':False,'game_or_PhysX_or_threads_tested':False,'FPS_measured':False}
args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))
