"""093非编译验证：真实CPP分支AST、参数逐位等价、原骨架局部数量复用与旧搜索对照。"""
from pathlib import Path
from types import SimpleNamespace as NS
import argparse,ast,configparser,copy,itertools,json,math,random,re,struct,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from test_interface_probe092 import VM as OldVM,Env,interface_cases,experiment_cases,existing_scope_clock_cases,part_names
from test_work_trace091 import normal
from test_performance080 import Program,Returned
from test_native_profile084 import definitions
from test_medical_gate083 import replay

def text(p):return p.read_text('utf8')
def bits(v):return struct.pack('<'+'f'*len(v),*v)
def f32(v):return struct.unpack('<f',struct.pack('<f',v))[0]
class Vector(list):
 def size(self):return len(self)
 def assign(self,n,value):self[:]=[copy.deepcopy(value) for _ in range(n)]
class It:
 def __init__(self,items):self.items=items;self.at=0
 def hasMoreElements(self):return self.at<len(self.items)
 def getNext(self):x=self.items[self.at];self.at+=1;return x
class Name(str):
 def find(self,s):
  v=super().find(s);return v if v>=0 else 2**64-1
class Continued(Exception):pass
class Broken(Exception):pass
class VM(OldVM):
 def expr(self,n,e):
  if n.type=='delete_expression':
   value=self.expr(n.named_children[-1],e)
   if value:value.free()
   return None
  if n.type=='new_expression':
   arguments=next(x for x in n.named_children if x.type=='argument_list')
   return e['allocate_cache'](self.expr(arguments.named_children[0],e))
  if n.type=='string_literal':return ast.literal_eval(self.txt(n))
  if n.type=='call_expression':
   f=self.txt(n.child_by_field_name('function'))
   if f.startswith(('static_cast<','dynamic_cast<')):
    v=self.expr(n.child_by_field_name('arguments').named_children[0],e)
    return v if not f.startswith('dynamic_cast') or getattr(v,'tagpoint',False) else None
  if n.type=='binary_expression':
   a=n.child_by_field_name('left');b=n.child_by_field_name('right');op=self.source[a.end_byte:b.start_byte].decode().strip()
   if op=='<<':return self.expr(a,e)<<self.expr(b,e)
   if op=='+':
    av,bv=self.expr(a,e),self.expr(b,e)
    if isinstance(av,list) and isinstance(bv,int):return av[bv:]
   if op=='|':return self.expr(a,e)|self.expr(b,e)
   if op in ['==','!=']:
    av,bv=self.expr(a,e),self.expr(b,e)
    if isinstance(av,NS) and isinstance(bv,NS):return (av is bv) if op=='==' else (av is not bv)
  if n.type=='assignment_expression':
   a=n.child_by_field_name('left');b=n.child_by_field_name('right');op=self.source[a.end_byte:b.start_byte].decode().strip()
   if op=='|=':
    v=self.expr(a,e)|self.expr(b,e);self.assign(a,e,v);return v
  if n.type=='sizeof_expression':return 4 if 'float' in self.txt(n) else 16
  return super().expr(n,e)
 def statement(self,n,e):
  if n.type=='try_statement':
   body=next(x for x in n.named_children if x.type=='compound_statement')
   try:return self.statement(body,e)
   except MemoryError:
    handler=next(x for x in n.named_children if x.type=='catch_clause' and 'std::bad_alloc' in self.txt(x))
    return self.statement(handler.child_by_field_name('body'),e)
  if n.type=='continue_statement':raise Continued()
  if n.type=='break_statement':raise Broken()
  if n.type in ['while_statement','for_statement']:
   initializer=n.child_by_field_name('initializer')
   if initializer:self.statement(initializer,e)
   condition=n.child_by_field_name('condition');update=n.child_by_field_name('update');guard=0
   while condition is None or self.expr(condition,e):
    try:self.statement(n.child_by_field_name('body'),e)
    except Continued:pass
    except Broken:break
    if update:self.expr(update,e)
    guard+=1;assert guard<100000
   return
  if n.type=='declaration' and 'IrisDiagnostics::InterfaceScope' in self.txt(n):return
  return super().statement(n,e)

def strip_observers(s):
 """仅用于比较/解释，绝不用语法器移除__fastcall后的文本写回产品。"""
 s=normal(s);p=Program(s);edits=[];variables=[]
 for n in p.nodes('declaration'):
  t=p.txt(n)
  if re.match(r'IrisDiagnostics::InterfaceScope\s+',t):
   variables+=re.findall(r'IrisDiagnostics::InterfaceScope\s+(\w+)',t);edits.append((n.start_byte,n.end_byte,b''))
 for n in p.nodes('compound_statement'):
  code=[x for x in n.named_children if x.type!='comment']
  if n.parent and n.parent.type!='function_definition' and code and code[0].type=='declaration' and re.match(r'IrisDiagnostics::InterfaceScope\s+(?:submitTiming|executeTiming|finishTiming|recoveryTiming|animationScan)',p.txt(code[0])):
   edits.extend([(n.start_byte,n.start_byte+1,b''),(n.end_byte-1,n.end_byte,b'')])
 b=p.source
 for a,z,v in sorted(edits,reverse=True):b=b[:a]+v+b[z:]
 out=b.decode()
 for var in variables:out=re.sub(r'\b'+var+r'\.(?:Finish|Switch)\([^;]*\);','',out)
 out=out.replace('bool overlap;\n                overlap=hit.hitShape->checkOverlapSphere(initial);\n                if(!overlap)', 'if(!hit.hitShape->checkOverlapSphere(initial))')
 out=out.replace('if(pending)Finish();','if(pending){query->execute();query->finish(true);}')
 return out

def preservation(before):
 total=0
 for f,skip in [('native/NativeMultiContact.cpp',set()),('IrisArsenal.cpp',{'ActualWeapon','ReadAssets'}),('IrisCombat.cpp',{'Visual','Clear','Create','Draw','Configure'})]:
  raw=text(ROOT/f);oldraw=text(before/f);assert raw.count('__fastcall')==oldraw.count('__fastcall')
  a,b=Program(strip_observers(oldraw)),Program(strip_observers(raw))
  for node in a.nodes('function_definition'):
   body=node.child_by_field_name('body');head=a.source[node.start_byte:body.start_byte].decode()
   if any(re.search(r'\b'+name+r'\s*\(',head) for name in skip):continue
   matches=[n.child_by_field_name('body') for n in b.nodes('function_definition') if b.source[n.start_byte:n.child_by_field_name('body').start_byte].decode()==head]
   assert matches and any(a.tokens(body)==b.tokens(x) for x in matches),(f,head)
   total+=1
 for f in ['IrisCombat.h','IrisRanged.cpp','IrisRanged.h','native/NativeMultiContact.h','native/FiniteCylinder.h','IrisNativeAudit.cpp','IrisNativeAudit.h','IrisWoundAudit.cpp','IrisWoundAudit.h']:
  assert (ROOT/f).read_bytes()==(before/f).read_bytes(),f
 return total

def weapon_cases():
 p=VM(strip_observers(text(ROOT/'IrisArsenal.cpp')));fast=definitions(p,'ActualWeapon');legacy=definitions(p,'ActualWeaponLegacy')
 rng=random.Random(93044);cases=0;old_getters=0;new_getters=0
 for n in [0,1,3,20,128,255,256,257,300]:
  for scenario in range(36):
   body=NS();bones=[];calls=[0]
   for i in range(n):
    b=NS(tagpoint=False,children=[])
    def count(b=b):calls[0]+=1;return len(b.children)
    b.numChildren=count;b.getChild=lambda j,b=b:b.children[j];bones.append(b)
   for i in range(max(0,n-1)):bones[i].children.append(bones[i+1])
   for i in range(rng.randrange(0,18)):
    if not bones:break
    parent=bones[rng.randrange(n)];tag=NS(tagpoint=True);owner=body if rng.random()<.9 else NS()
    tag.getParentEntity=lambda owner=owner:owner;obj=NS();tag.getChildObject=lambda obj=obj:obj
    name=Name('iris_weapon.mesh' if rng.random()<.2 else 'hat.mesh');visible=rng.random()<.85;attached=rng.random()<.9
    obj.getMovableType=lambda:'Entity';obj.isAttached=lambda attached=attached:attached;obj.isVisible=lambda visible=visible:visible
    obj.getMesh=lambda name=name:NS(getName=lambda:name);parent.children.append(tag)
   if scenario%7==0 and bones:bones[0].children[:0]=[NS(tagpoint=False) for _ in range(520)]
   animation=NS(body=body,skeleton=NS(getBoneIterator=lambda:It(bones)));character=NS(animation=animation)
   env=dict(c=character,attachmentCountReuse=True,**{'IrisDiagnostics::CollisionProfileEnabled':lambda:False,'std::string::npos':2**64-1})
   env['ActualWeaponLegacy']=lambda a:p.run(legacy,dict(env,a=a))
   calls[0]=0;expected=p.run(legacy,dict(env,a=animation));old_getters+=calls[0]
   calls[0]=0;actual=p.run(fast,env);new_getters+=calls[0];assert actual is expected,(n,scenario)
   env['attachmentCountReuse']=False;assert p.run(fast,env) is expected
   cases+=2
 for attr in ['body','skeleton']:
  a=NS(body=NS(),skeleton=NS());setattr(a,attr,None)
  assert p.run(fast,dict(c=NS(animation=a))) in (None,0);cases+=1
 assert new_getters<old_getters
 return dict(actual_CPP_AST_cases=cases,order_and_budget_edges_preserved=True,no_cross_frame_cache=True,old_child_count_calls=old_getters,new_child_count_calls=new_getters)

def attachment_API_check(before):
 # 不通过禁用宏启用Entity接口，也不使用与本机返回容器ABI不同的OldNode迭代器。
 current=text(ROOT/'IrisArsenal.cpp');old=text(before/'IrisArsenal.cpp')
 assert 'getAttachedObjectIterator' not in current and 'getChildIterator' not in current
 a=Program(old);b=Program(current)
 oldcalls=set(re.findall(r'->(\w+)\(',a.txt(definitions(a,'ActualWeapon'))))
 newcalls=set(re.findall(r'->(\w+)\(',b.txt(definitions(b,'ActualWeapon'))))
 assert newcalls<=oldcalls,(newcalls-oldcalls)
 sdk=Path('E:/KenshiProject/1.Dependencies/KenshiLib_0.5.0')
 dll=Path('D:/steam/steamapps/common/Kenshi/OgreMain_x64.dll').read_bytes()
 lib=(sdk/'Libraries/OgreMain_x64.lib').read_bytes()
 entity=(sdk/'Include/ogre/OgreEntity.h').read_text('utf8')
 assert '#ifdef ENABLE_INCOMPATIBLE_OGRE_2_0' in entity[:entity.index('getAttachedObjectIterator')]
 assert b'?getAttachedObjectIterator@Entity@Ogre@@' not in dll
 assert b'?getAttachedObjectIterator@Entity@Ogre@@' not in lib
 pattern=rb'\?getChildIterator@OldNode@Ogre@@[^\x00\x20\r\n]+'
 game=set(re.findall(pattern,dll));imports=set(re.findall(pattern,lib))
 assert game and imports and not game.intersection(imports)
 return dict(no_new_Ogre_method=True,disabled_Entity_iterator_avoided=True,mismatched_OldNode_iterator_avoided=True,SDK_real_binary_checked=True)


def parameter_cases():
 c=text(ROOT/'IrisCombat.cpp');p=VM(c);cache_struct=next(n for n in p.nodes('struct_specifier') if p.txt(n.child_by_field_name('name'))=='ParameterCache')
 same=next(n.child_by_field_name('body') for n in p.nodes('function_definition') if cache_struct.start_byte<n.start_byte<n.end_byte<cache_struct.end_byte and 'bool Same(' in p.source[n.start_byte:n.child_by_field_name('body').start_byte].decode())
 store=definitions(p,'Store');submit=definitions(p,'SubmitParameter')
 # 执行Draw实际分组提交分支；旧分支也直接来自092源码，用于逐参数比较。
 draw=next(n for n in p.nodes('function_definition') if 'void Draw(' in p.source[n.start_byte:n.child_by_field_name('body').start_byte].decode())
 branch=next(n for n in p.nodes('if_statement') if draw.start_byte<n.start_byte<n.end_byte<draw.end_byte and p.txt(n.child_by_field_name('condition'))=='(parameterCache)')
 masks=json.loads((TASK/'curve-constant-masks.json').read_text('utf8'))
 tokens=iter((ROOT/'package/IrisArsenal/assets/effect_curves.csv').read_text('utf8').split());next(tokens);next(tokens);count=int(next(tokens));assets=[]
 for _ in range(count):
  key=next(tokens);subs=int(next(tokens));samples=int(next(tokens));duration=float(next(tokens));next(tokens)
  tracks=[[[f32(float(next(tokens))) for k in range(25)] for frame in range(samples)] for layer in range(subs)]
  assets.append((key,subs,samples,duration,tracks))
 cases=0;writes=0;possible=0;rounded_changes=0;producer_checks=0
 source_decl=re.search(r'    static const unsigned begin\[7\]=\{([^}]+)\},width\[7\]=\{([^}]+)\};',c)
 assert source_decl
 starts=list(map(int,source_decl[1].split(',')));widths=list(map(int,source_decl[2].split(',')))
 producer=VM(c.replace(source_decl[0],''));build=definitions(producer,'BuildParameterGroups')
 class Cache:
  def __init__(self,mask):self.layers=[NS(mask=mask,valid=0,values=[None]*7)]
  def Same(self,layer,group,value):return p.run(same,dict(layers=self.layers,layer=layer,group=group,value=value,**{'std::memcmp':lambda a,b,n:0 if bits(a)==bits(b) else 1}))
  def Store(self,layer,group,value):return p.run(store,dict(layers=self.layers,layer=layer,group=group,value=value))
 for key,subs,samples,duration,tracks in assets:
  asset=NS(tracks=Vector([Vector([NS(value=frame) for frame in layer]) for layer in tracks]),samples=samples,constantGroups=Vector())
  producer.run(build,dict(asset=asset,begin=starts,width=widths,**{'std::memcmp':lambda a,b,n:0 if bits(a[:n//4])==bits(b[:n//4]) else 1}))
  assert list(asset.constantGroups)==masks[key],key;producer_checks+=1
  for layer in range(subs):
   cache=Cache(masks[key][layer]);actual={};expected={}
   def setter(i,value):actual[i]=list(value)
   sub=NS(setCustomParameter=setter)
   def call(sub,cache,layer,group,index,value):return p.run(submit,dict(sub=sub,cache=cache,layer=layer,group=group,index=index,value=value))
   for t in [0.,.01,.11,.21,.333,.5,.7,.9,1.,.5,.5,0.]:
    x=f32(f32(t)*f32(samples-1));lo=min(samples-1,int(x));hi=min(samples-1,lo+1);u=f32(x-lo)
    v=[f32(f32(tracks[layer][lo][k]*f32(1-u))+f32(tracks[layer][hi][k]*u)) for k in range(25)]
    env=dict(parameterCache=cache,parameterWrites=0,sub=sub,i=0,v=v,SubmitParameter=call,**{'Ogre::Vector4':lambda *v:list(v)})
    p.statement(branch,env);writes+=env['parameterWrites'];possible+=7
    oldenv=dict(env,parameterCache=None,parameterWrites=0,sub=NS(setCustomParameter=lambda i,v:expected.__setitem__(i,list(v))))
    p.statement(branch,oldenv)
    assert {k:bits(v) for k,v in actual.items()}=={k:bits(v) for k,v in expected.items()},(key,layer,t)
    assert oldenv['parameterWrites']==7;cases+=1
 # 异常必须不能提交缓存；失败重试仍会调用setter。动态组、符号零也要逐位区分。
 failure_checks=0
 for mask in [0,127]:
  cache=Cache(mask);seen=[]
  def fail(i,v):seen.append(i);raise RuntimeError('setter')
  try:call(NS(setCustomParameter=fail),cache,0,0,2,[1.,0.,0.,0.])
  except RuntimeError:pass
  else:raise AssertionError('setter failure not forwarded')
  assert cache.layers[0].valid==0
  call(NS(setCustomParameter=lambda i,v:seen.append(i)),cache,0,0,2,[1.,0.,0.,0.]);assert seen==[2,2]
  call(NS(setCustomParameter=lambda i,v:seen.append(i)),cache,0,0,2,[1.,-0.,0.,0.]);assert seen==[2,2,2];failure_checks+=1
 return dict(actual_Draw_branch_AST_cases=cases,actual_BuildParameterGroups_assets=producer_checks,constant_masks=masks,old_group_writes=possible,new_group_writes=writes,saved=possible-writes,bitwise_equal_after_every_update=True,setter_failure_and_signed_zero_cases=failure_checks)

def ownership_cases():
 p=VM(text(ROOT/'IrisCombat.cpp'));visual=next(n for n in p.nodes('struct_specifier') if p.txt(n.child_by_field_name('name'))=='Visual')
 clear=next(n.child_by_field_name('body') for n in p.nodes('function_definition') if visual.start_byte<n.start_byte<n.end_byte<visual.end_byte and 'void Clear(' in p.source[n.start_byte:n.child_by_field_name('body').start_byte].decode())
 create=next(n for n in p.nodes('function_definition') if visual.start_byte<n.start_byte<n.end_byte<visual.end_byte and 'void Create(' in p.source[n.start_byte:n.child_by_field_name('body').start_byte].decode())
 allocation=next(n for n in p.nodes('if_statement') if create.start_byte<n.start_byte<n.end_byte<create.end_byte and p.txt(n.child_by_field_name('condition'))=='(parameterGroupReuse&&a->second.samples)')
 cases=0
 for alive,scene_valid in itertools.product([False,True],repeat=2):
  for transfers in [0,1,16,128]:
   freed=[];objects=[];cache=NS(free=lambda:freed.append('cache'))
   value=NS(entity=NS(),node=NS(),key='beam',parametersValid=True,parameterCache=cache)
   # 和既有Visual手动所有权一样按值转移，仅最终Owner调用Clear；不使用自动释放析构。
   for _ in range(transfers):value=NS(**vars(value))
   scene=NS(destroyEntity=lambda e:objects.append(e),destroySceneNode=lambda n:objects.append(n)) if scene_valid else None
   env=Env(value,dict(alive=alive,scene=scene,**{'IrisDiagnostics::Add':lambda *v:None,'IrisDiagnostics::DISPOSED_VISUALS':0}))
   # node的detach与key.clear都是当前对象自己的操作。
   value.node.detachAllObjects=lambda:None
   class Key(str):
    def clear(self):pass
   value.key=Key('beam');env['key']=value.key
   p.run(clear,env);p.run(clear,env)
   assert freed==['cache'] and value.parameterCache==0 and value.entity==value.node==0
   assert len(objects)==(2 if alive and scene_valid else 0);cases+=1
 for enabled,samples,mask,fail in itertools.product([False,True],[0,2],[0,12],[False,True]):
  calls=[];count=[];v=NS(parameterCache=0)
  def allocate(masks):
   calls.append('allocate')
   if fail:raise MemoryError('optional cache')
   return NS(masks=list(masks))
  asset=NS(samples=samples,constantGroups=Vector([mask]));env=Env(v,dict(parameterGroupReuse=enabled,a=NS(second=asset),allocate_cache=allocate,**{'IrisDiagnostics::Add':lambda *v:count.append(v),'IrisDiagnostics::PARAMETER_CACHE_FALLBACKS':0}))
  p.statement(allocation,env);needed=bool(enabled and samples and mask)
  assert len(calls)==int(needed)
  assert len(count)==int(needed and fail)
  assert bool(v.parameterCache)==bool(needed and not fail);cases+=1
 return dict(actual_Clear_AST_and_manual_transfer_cases=16,actual_optional_allocation_AST_cases=16,total=cases,allocation_failure_original_path=True,no_extra_allocation_when_disabled=True)

def gates(d):
 p=VM(normal(d));body=definitions(p,'QueryBoundaryPart');cases=0
 for option,enabled,part in itertools.product([False,True],[False,True],[0,38,44]):
  observed=[]
  def enabled_fn():observed.append('enabled');return enabled
  value=p.run(body,dict(queryBoundaryOption=option,part=part,IF_PART_COUNT=45,InterfaceEnabled=enabled_fn))
  assert value==(part if option and enabled else 45)
  assert observed==(['enabled'] if option else []);cases+=1
 return dict(actual_AST_cases=cases,disabled_short_circuit=True)

def main(before,out):
 global TASK
 TASK=out.parent
 result=dict(original_preserved_functions=preservation(before),weapon=weapon_cases(),attachment_API=attachment_API_check(before),parameters=parameter_cases())
 d=text(ROOT/'IrisDiagnostics.cpp');h=text(ROOT/'IrisDiagnostics.h')
 result.update(ownership=ownership_cases(),interface_tree=interface_cases(d,h),experiment=experiment_cases(d),reused_clocks=existing_scope_clock_cases(d),boundary_gate=gates(d))
 result['medical_FIFO']=replay(re.sub(r'workTrace\.Mark\([^;]+\);','',strip_observers(text(ROOT/'IrisCombat.cpp'))))
 units=[]
 for f in list(ROOT.glob('*.cpp'))+list(ROOT.glob('*.h'))+list((ROOT/'native').glob('*.cpp'))+list((ROOT/'native').glob('*.h')):
  s=normal(text(f));s=re.sub(r'typedef Item\*\(RootObjectFactory::\* CreateMember\)\([^;]+;','typedef void* CreateMember;',s);Program(s);units.append(str(f.relative_to(ROOT)))
 assert len(re.findall(r'"[^"]+"',re.search(r'interfaceNames\[IF_PART_COUNT\]=\{([^}]+)\}',d)[1]))==len(part_names(h))==45
 for n in ['distribution/IrisArsenal.ini','package/IrisArsenal/IrisArsenal.ini']:
  c=configparser.ConfigParser();c.read(ROOT/n,encoding='utf8');cfg=c['IrisArsenal']
  for k in ['EnableQueryBoundaryProfiling','EnableAttachmentCountReuse','EnableVisualParameterGroupReuse']:assert cfg[k]=='1'
  assert cfg['EnableRangedSingleProbeABTest']=='0' and cfg['EnableRangedSingleEmptyProbe']=='1'
  assert cfg['DamageFlushBudgetMs']=='2.5' and cfg['DamageFlushMaxHits']=='32'
 for n in ['tools/stage_package.py','tools/test_update_mod.py','tools/test_query_boundary093.py']:ast.parse(text(ROOT/n))
 from stage_package import validate_dll
 try:validate_dll()
 except RuntimeError as e:assert '093查询边界和实例精确复用' in str(e);result['old_DLL_rejected']=str(e)
 else:raise AssertionError('旧DLL不得冒充093')
 result.update(grammar_units=units,compiled=False,real_Windows_TLS_PhysX_or_threads_or_game=False,FPS_measured=False)
 out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--before',type=Path,required=True);a.add_argument('--out',type=Path,required=True);v=a.parse_args();main(v.before,v.out)
