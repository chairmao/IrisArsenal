"""080非编译验收：执行实际CPP分支AST，对照原结果消费者；不运行PhysX/游戏线程。"""
from pathlib import Path
from types import SimpleNamespace as NS
import argparse,copy,itertools,json,math,random,re,struct,sys
ROOT=Path(__file__).resolve().parents[1]
from test_native_melee072 import Branches,Returned,tree_sitter,tree_sitter_cpp
class Program(Branches):
 def __init__(self,text):
  self.source=re.sub(r'\b__fastcall\b','',text).encode();self.tree=tree_sitter.Parser(tree_sitter.Language(tree_sitter_cpp.language())).parse(self.source);assert not self.tree.root_node.has_error
 def nodes(self,kind):
  def visit(n):
   if n.type==kind:yield n
   for c in n.named_children:yield from visit(c)
  return list(visit(self.tree.root_node))
 def body(self,name):
  found=[n.child_by_field_name('body') for n in self.nodes('function_definition') if re.search(r'\b'+re.escape(name)+r'\s*\(',self.source[n.start_byte:n.child_by_field_name('body').start_byte].decode())]
  assert len(found)==1,(name,len(found));return found[0]
 def tokens(self,node):
  out=[]
  def walk(n):
   if n.type=='comment':return
   if not n.children:out.append(self.txt(n))
   for c in n.children:walk(c)
  walk(node);return out
 def expr(self,n,e):
  kind=n.type
  if kind=='number_literal':
   x=re.sub('[fFuUlL]+$','',self.txt(n));return float(x) if '.' in x or 'e' in x.lower() else int(x,0)
  if kind=='sizeof_expression':return len(e['inputs'])
  if kind=='subscript_expression':return self.expr(n.child_by_field_name('argument'),e)[self.expr(n.child_by_field_name('indices').named_children[0],e)]
  if kind=='assignment_expression':
   left=n.child_by_field_name('left');right=n.child_by_field_name('right');op=self.source[left.end_byte:right.start_byte].decode().strip();v=self.expr(right,e)
   if op=='+=':v=self.expr(left,e)+v
   else:assert op=='='
   self.assign(left,e,copy.deepcopy(v));return v
  if kind=='update_expression':
   arg=n.named_children[0];v=self.expr(arg,e)+1;self.assign(arg,e,v);return v
  if kind=='binary_expression':
   l=n.child_by_field_name('left');r=n.child_by_field_name('right');op=self.source[l.end_byte:r.start_byte].decode().strip()
   if op in ('>','<','>=','<='):
    a=self.expr(l,e);b=self.expr(r,e);return {'>':lambda:a>b,'<':lambda:a<b,'>=':lambda:a>=b,'<=':lambda:a<=b}[op]()
  if kind=='call_expression':
   name=self.txt(n.child_by_field_name('function'));args=n.child_by_field_name('arguments').named_children
   if name in ('RayBlocker','SweepAll'):return e[name](e)
  return super().expr(n,e)
 def assign(self,n,e,v):
  if n.type=='identifier':e[self.txt(n)]=v
  elif n.type=='field_expression':setattr(self.expr(n.child_by_field_name('argument'),e),self.txt(n.child_by_field_name('field')),v)
  else:raise AssertionError(('assign',self.txt(n)))
 def statement(self,n,e):
  if n.type=='expression_statement':
   if n.named_children:self.expr(n.named_children[0],e)
   return
  return super().statement(n,e)
 def execute(self,body,e):
  try:self.statement(body,e)
  except Returned as x:return x.value
  raise AssertionError('没有return')
def function_text(text,name):
 p=Program(text);return p.tokens(p.body(name))
def main(before):
 current=(ROOT/'IrisCombat.cpp').read_text('utf8');old=(before/'IrisCombat.cpp').read_text('utf8');native=(ROOT/'native/NativeMultiContact.cpp').read_text('utf8');oldnative=(before/'native/NativeMultiContact.cpp').read_text('utf8')
 cp,op,np,on=Program(current),Program(old),Program(native),Program(oldnative)
 native_body=np.body('ProjectileAll');old_body=on.body('ProjectileAll');query_cases=0;shortcuts=0
 def run_query(program,body,wall,radius,ray_status=0,sweep_status=0):
  terrain=NS(count=0,items=[],diagnostic=NS(uniqueBeforeFailure=0,received=0,terrain=NS(hit=0)))
  chars=NS(count=99,items=[],diagnostic=NS(uniqueBeforeFailure=99,received=0,terrain=NS(hit=0)))
  e={'world':object(),'from':object(),'motion':object(),'radius':radius,'groups':0xffffffff,'characters':chars,'terrain':terrain,'queryCalls':0,'QUERY_COMPLETE':0,'Finite':math.isfinite}
  def ray(env):
   env['queryCalls']=1;terrain.count=int(wall is not None and ray_status==0);terrain.items=[NS(fraction=wall)] if terrain.count else [];terrain.diagnostic.uniqueBeforeFailure=terrain.count;terrain.diagnostic.received=terrain.count;terrain.diagnostic.terrain.hit=terrain.count;return ray_status
  def sweep(env):
   env['swept']=1;chars.count=3 if sweep_status==0 and math.isfinite(radius) and radius>0 else 0;chars.diagnostic=NS(uniqueBeforeFailure=chars.count,received=chars.count,terrain=NS(hit=0));return 3 if not math.isfinite(radius) or radius<=0 else sweep_status
  e.update(RayBlocker=ray,SweepAll=sweep)
  return program.execute(body,e),e['queryCalls'],chars.count,terrain.count
 for wall,radius,ray_status,sweep_status in itertools.product((None,0.,-0.,1e-12,.25,1.),(4.5,1.,0.,-1.,float('nan'),float('inf')),range(5),range(5)):
  a=run_query(on,old_body,wall,radius,ray_status,sweep_status);b=run_query(np,native_body,wall,radius,ray_status,sweep_status);fast=ray_status==0 and wall==0 and wall is not None and math.isfinite(radius) and radius>0
  if fast:
   assert b==(0,1,0,1);shortcuts+=1
   # t=0环境已经决定命中；不再执行的角色查询无法产生更早的合法TOI。
   assert all(not f<0 for f in (0,1e-9,.5,1))
  else:assert a==b,(wall,radius,ray_status,sweep_status,a,b)
  query_cases+=1
 # 快路之外的原生查询函数全部原样，失败/排序/初始重叠和圆柱不动。
 protected_native=['RayBlocker','SweepAll','OverlapSphere','OverlapCapsule','OverlapCapsules','CylinderAll','ReadObjectKey']
 for name in protected_native:assert function_text(native,name)==function_text(oldnative,name),name
 # 实际资格缓存方法和实际新旧消费者条件；各查询期间关系固定，不跨查询复用。
 memo_body=cp.body('Ignore');old_condition=next(n.child_by_field_name('condition') for n in op.nodes('if_statement') if op.txt(n.child_by_field_name('condition')).startswith('(c==caster||'))
 new_condition=next(n.child_by_field_name('condition') for n in cp.nodes('if_statement') if 'split?contactMemo.Ignore' in cp.txt(n.child_by_field_name('condition')))
 class Character:pass
 caster=Character();caster.key=(True,11,1,1,0,1)
 def key_obj(k):return NS(**dict(zip(('present','type','container','containerSerial','index','serial'),k)))
 def choose(program,condition,contacts,wall,allowed,split,memo=False):
  resolves=0;checks=0;objects={};state={'valid':False,'ignored':False,'checks':0,'reuses':0};target='wall' if wall is not None else None;f=wall if wall is not None else 1.
  def resolve(k):
   nonlocal resolves
   resolves+=1
   if k==caster.key:return caster
   if k not in objects:o=Character();o.key=k;objects[k]=o
   return objects[k]
  def ignore(owner,c):
   nonlocal checks
   checks+=1;return c.key not in allowed
  for k,frac in contacts:
   h=NS(getCharacter=lambda k=k:resolve(k));e={'caster':caster,'s':NS(move=5 if split else 0),'split':split,'h':h,'RangedMove':lambda m:m in (5,6,7),'IgnoreRangedContact':ignore}
   if memo:
    def use_cache(owner,key,identity):
     state.update(caster=owner,key=key,identity=identity,IgnoreRangedContact=ignore)
     return cp.execute(memo_body,state)
    e['contactMemo']=NS(Ignore=use_cache);e['hits']=NS(items=[NS(object=key_obj(k))]);e['k']=0
   else:e['c']=h.getCharacter()
   if program.expr(condition,e):continue
   if target is None or frac<f:target=k;f=frac
   break
  return (target,f),resolves,checks,state['reuses']
 rng=random.Random(80079);scenes=0;reuses=0
 keys=[caster.key]+[(True,11,1,1,i,1) for i in range(1,18)]
 for _ in range(4096):
  contacts=sorted([(rng.choice(keys),rng.choice([0.,.1,.2,.5,.9,1.])) for _ in range(rng.randrange(65))],key=lambda x:x[1]);wall=rng.choice([None,0.,.2,.5,1.]);allowed={k for k in keys if rng.randrange(5)==0};split=bool(rng.randrange(2))
  a=choose(op,old_condition,contacts,wall,allowed,split);b=choose(cp,new_condition,contacts,wall,allowed,split,True)
  assert a[0]==b[0] and b[1]<=a[1] and b[2]<=a[2],(a,b);scenes+=1;reuses+=b[3]
 # 五字段+present逐项不同都必须重新判定；同index/serial不能冒充完整身份相等。
 key=keys[1];e={'valid':False,'ignored':False,'checks':0,'reuses':0,'caster':caster,'IgnoreRangedContact':lambda c,v:True};who=Character()
 for variant in [key,key]+[tuple((not value if i==0 else value+1) if i==axis else value for i,value in enumerate(key)) for axis in range(6)]:
  e.update(key=key_obj(variant),identity=NS(getCharacter=lambda:who));cp.execute(memo_body,e)
 assert e['checks']==7 and e['reuses']==1
 # 新查询重建memo；敌对/盟友或昏迷变化不会沿用上一查询结果。
 assert choose(cp,new_condition,[(key,0.)],None,{key},True,True)[0][0]==key
 assert choose(cp,new_condition,[(key,0.)],None,set(),True,True)[0][0] is None
 # 参数插值/写入体逐token一致，执行真实memcmp条件检查位级复用，保留-0和NaN载荷。
 def parameter_loop(p):return next(n for n in p.nodes('for_statement') if 'VisualLayerAge' in p.txt(n) and 'setCustomParameter' in p.txt(n))
 assert cp.tokens(parameter_loop(cp))==op.tokens(parameter_loop(op))
 predicate=next(n.child_by_field_name('value') for n in cp.nodes('init_declarator') if cp.txt(n.child_by_field_name('declarator'))=='updateParameters')
 last=b'\0'*12;valid=False;cache_cases=0;skipped=0
 inputs_list=[last,last,struct.pack('<fff',-0.,0.,0.),struct.pack('<III',0x7fc00001,0,0),struct.pack('<III',0x7fc00001,0,0)]+[rng.randbytes(12) for _ in range(1024)]
 for data in inputs_list:
  env={'parametersValid':valid,'parameterInputs':last,'inputs':data,'std::memcmp':lambda a,b,n:0 if a[:n]==b[:n] else 1}
  update=cp.expr(predicate,env);assert bool(update)==(not valid or data!=last)
  if update:last=data;valid=True
  else:skipped+=1
  assert last==data;cache_cases+=1
 assert skipped>=2
 assert 'key.clear();parametersValid=false;' in current
 assert 'parameterInputs[0]=parameterInputs[1]=parameterInputs[2]=0' in current
 draw=cp.txt(cp.body('Draw'));assert draw.index('node->setScale')<draw.index('updateParameters')<draw.index('entity->setVisible')
 assert 'setCustomParameter(9' not in draw and 'spinning?1.f:0.f' in current
 # 实际新旧可见谓词：默认模式逐值相同；诊断隐藏始终false，不改变CPU年龄或参数输入。
 def visible(p,own):
  return next(n.child_by_field_name('arguments').named_children[0] for n in p.nodes('call_expression') if p.txt(n.child_by_field_name('function'))=='entity->setVisible' and (('diagnosticHideEffects' in p.txt(n)) if own else ('opacity>' in p.txt(n))))
 for opacity in (-1.,0.,.001,.001001,1.,float('nan')):
  assert cp.expr(visible(cp,True),{'opacity':opacity,'diagnosticHideEffects':False})==op.expr(visible(op,False),{'opacity':opacity})
  assert cp.expr(visible(cp,True),{'opacity':opacity,'diagnosticHideEffects':True}) is False
 # 光炮只删除查询前一次写入，最终帧参数仍在查询后提交；全部独立年龄/医疗代码保持。
 assert 'DrawBeam(r,origin);' not in cp.txt(cp.body('AdvanceEffects'))
 tick=cp.txt(cp.body('Tick'));assert tick.index('AdvanceEffects(')<tick.index('ResolveJobs(')<tick.index('DrawBeam(residues[i],origin)')
 protected=['DamagePolicyReason','CanDamage','IgnoreRangedContact','Collect','Flush','DamageOutcome','ProtectedMeleeMove','ProtectedRangedMove','Choose','PickRanged','Muzzle','DrawBeam','ElectroFrame','WingCenter','Blast','Emit','End']
 checked=[]
 for name in protected:
  assert function_text(current,name)==function_text(old,name),name;checked.append(name)
 for rel in ('package/IrisArsenal/IrisArsenal.ini','distribution/IrisArsenal.ini'):
  import configparser
  a=configparser.ConfigParser();a.read(before/rel,encoding='utf8');b=configparser.ConfigParser();b.read(ROOT/rel,encoding='utf8');assert b.get('IrisArsenal','DiagnosticHideEffects')=='0';b.remove_option('IrisArsenal','DiagnosticHideEffects');assert {k:dict(a[k]) for k in a.sections()}=={k:dict(b[k]) for k in b.sections()}
 # 自有日志索引仅末尾追加，不将新值插入旧状态/掩码域；名称数组长度与枚举一一匹配。
 header=(ROOT/'IrisDiagnostics.h').read_text('utf8');oldheader=(before/'IrisDiagnostics.h').read_text('utf8');diag=(ROOT/'IrisDiagnostics.cpp').read_text('utf8')
 for enum,array,count in [('Kind','names','KIND_COUNT'),('Counter','counters','COUNTER_COUNT')]:
  def members(x):return [v.strip() for v in re.search(r'enum '+enum+r'\s*\{([^}]+)\}',x).group(1).split(',')][:-1]
  a,b=members(oldheader),members(header);assert b[:len(a)]==a
  names=re.findall(r'"([^"]+)"',re.search(r'\b'+array+r'\['+count+r'\]\s*=\{([^}]+)\}',diag).group(1));assert len(names)==len(b)
 result={'native_AST_cases':query_cases,'zero_wall_shortcuts':shortcuts,'query_consumption_scenes':scenes,'observed_adjacent_reuses':reuses,'full_identity_field_boundaries':6,'parameter_AST_cases':cache_cases,'unchanged_native_functions':protected_native,'unchanged_combat_functions':checked,'normal_visual_default_preserved':True,'same_tick_only':True,'compiled':False,'game_visuals_or_threads_tested':False,'validation':'actual CPP AST with mocked API, protected token comparison, independent result consumer'}
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();r=main(a.before)
 with a.out.open('x',encoding='utf8') as f:json.dump(r,f,ensure_ascii=False,indent=2)
 print(json.dumps(r,ensure_ascii=False,indent=2))
