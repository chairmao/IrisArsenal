"""078非编译验证：16入口业务token对照、关闭路径AST、原子/采样/摘要边界。

没有运行C++线程或游戏；原子累计结构检查不等于引擎线程压力测试。
"""
from pathlib import Path
import argparse,json,re
from test_native_melee072 import tree_sitter,tree_sitter_cpp
from test_hook_fast076 import Execute
ROOT=Path(__file__).resolve().parents[1]
HOOKS={
 'IrisArsenal.cpp':{'ChooseHook':'CHOOSE','StartHook':'START','RunHook':'RUN','FrameHook':'FRAME','SafeHook':'SAFE'},
 'IrisCombat.cpp':{'MeleeBlockCheckHook':'BLOCK','MeleeStumbleHook':'STUMBLE','VulcanDefenceHook':'DEFENCE'},
 'IrisRanged.cpp':{name:'RANGED_'+name[:-4].upper() for name in ['UseHook','HasHook','ScoreHook','WithinHook','GunHook','AnimationHook','ShotHook','ReloadHook']}}
# Animation在enum中使用全名，其他8个键均与实际安装入口一一对应。
def parsed(text):
 text=re.sub(r'\b__fastcall\b','',text);text=re.sub(r'__declspec\(align\(64\)\)','',text);data=text.encode()
 node=tree_sitter.Parser(tree_sitter.Language(tree_sitter_cpp.language())).parse(data).root_node;assert not node.has_error
 return data,node

def functions(text,names):
 data,node=parsed(text);found={}
 def visit(n):
  if n.type=='function_definition':
   body=n.child_by_field_name('body');head=data[n.start_byte:body.start_byte].decode()
   for name in names:
    if re.search(r'\b'+name+r'\s*\(',head):found[name]=body
  for c in n.named_children:visit(c)
 visit(node);assert set(found)==set(names)
 return data,found

def business_tokens(text,names):
 data,found=functions(text,names);result={}
 def visit(n,skip):
  if n.type=='comment':skip.append((n.start_byte,n.end_byte,''));return
  value=data[n.start_byte:n.end_byte].decode()
  if n.type=='declaration' and value.startswith('IrisDiagnostics::HookAudit audit('):skip.append((n.start_byte,n.end_byte,''));return
  if n.type=='declaration' and re.match(r'(?:Lock|Guard) (?:lock|guard)\(&audit\);',value):
   skip.append((n.start_byte,n.end_byte,value.replace('(&audit)','')));return
  for c in n.named_children:visit(c,skip)
 for name,body in found.items():
  skip=[];visit(body,skip);out=data[body.start_byte:body.end_byte]
  for a,b,value in sorted(skip,reverse=True):out=out[:a-body.start_byte]+value.encode()+out[b-body.start_byte:]
  # 两边重新解析并比较叶token，忽略审计声明、锁观察参数和注释后的所有业务条件/调用仍须一致。
  _,n=parsed('void check()'+out.decode())
  # 用字节切片保证中文/宽字符不会改变token边界。
  b=('void check()'+out.decode()).encode();tokens=[]
  def collect(node):
   if node.children:
    for c in node.children:collect(c)
   else:tokens.append(b[node.start_byte:node.end_byte])
  collect(n);result[name]=tokens
 return result

def main(before):
 observed=[]
 for rel,names in HOOKS.items():
  old=(before/rel).read_text('utf8');new=(ROOT/rel).read_text('utf8')
  assert business_tokens(old,names)==business_tokens(new,names),(rel,'业务token改变')
  data,found=functions(new,names)
  for name,kind in names.items():
   body=data[found[name].start_byte:found[name].end_byte].decode()
   assert body.count('IrisDiagnostics::HookAudit audit(')==1
   assert 'IrisDiagnostics::HOOK_'+kind+');' in body,(name,kind)
   observed.append(rel+':'+name)
  assert old.count('KenshiLib::AddHook(')==new.count('KenshiLib::AddHook(')
 h=(ROOT/'IrisDiagnostics.h').read_text('utf8');d=(ROOT/'IrisDiagnostics.cpp').read_text('utf8')
 enum=re.search(r'enum Hook \{([^}]+)\}',h).group(1);kinds=[x.strip()for x in enum.split(',')];assert kinds[-1]=='HOOK_COUNT' and len(kinds)==17 and len(set(kinds))==17
 labels=re.search(r'hookNames\[HOOK_COUNT\]=\{([^}]+)\}',d).group(1);assert len(re.findall(r'"([a-z_]+)"',labels))==16
 assert 'volatile LONGLONG value[H_FIELDS]' in d and '__declspec(align(64)) HookStats' in d
 assert 'InterlockedCompareExchange64' in d and 'hookPrevious[hook][field]=current[field]' in d
 audit_region=d[d.index('HookAudit::HookAudit'):d.index('static void HookSummary')]
 for forbidden in ['EnterCriticalSection','LeaveCriticalSection','TlsAlloc','CreateThread','new ','Log(','std::ostringstream']:
  assert forbidden not in audit_region,forbidden
 assert 'totalSampled=(ordinal-1)%hookSampleEvery==0' in audit_region
 assert 'sampled=(ordinal-1)%hookSampleEvery==0' in audit_region
 assert 'if(!active)return;' in audit_region and 'totalSampled?HookMicroseconds' in audit_region
 # 实际AST执行关闭时的构造/析构和锁方法：环境不提供任何QPC/原子/锁函数，误调用就失败。
 machine=Execute(d);data,node=parsed(d)
 def visit(n):
  if n.type=='function_definition':
   body=n.child_by_field_name('body');head=data[n.start_byte:body.start_byte].decode()
   if 'HookAudit::HookAudit(' in head:machine.functions['audit_ctor']=body
   elif 'HookAudit::~HookAudit(' in head:machine.functions['audit_dtor']=body
  for c in n.named_children:visit(c)
 visit(node)
 for method in ['audit_ctor','audit_dtor','BeforeLock','Acquired','BeforeUnlock']:
  machine.run(method,{'active':False,'sampled':False,'totalSampled':False})
 machine.run('HookSummary',{'hookAuditEnabled':False})
 # 样本索引与两路分类规格：全部调用与进锁序号独立，不能误把快退样本当进锁样本。
 samples=0
 for every in [1,2,16,128,65536]:
  for calls in [0,1,2,31,128,259,65537]:
   selected=[i for i in range(1,calls+1)if (i-1)%every==0]
   assert len(selected)==(calls+every-1)//every
   locked=[i for i in range(1,calls+1)if i%7==0]
   lock_samples=[i for i in range(1,len(locked)+1)if (i-1)%every==0]
   assert len(lock_samples)==(len(locked)+every-1)//every;samples+=1
 for label in ['calls_per_second=','callback_wall_ms_sampled=','sampled_no_audited_lock_callbacks=','locked_total_wall_ms_sampled=','max_callback_ms_process=','total_and_lock_samples_independent=1','includes_original=1','nested_timings_not_additive=1','elapsed_includes_pause=1']:
  assert label in d,label
 assert 'HookSummary(summaryId,windowElapsed,std::max(0.0,now-processBegin))' in d
 assert 'IRIS_HOOK_AUDIT_078' in d
 return {'hook_business_tokens_equal':observed,'hook_count':16,'new_installed_hooks':0,'disabled_actual_AST_methods_no_external_calls':6,'sample_boundaries':samples,'atomic_storage_no_new_lock_thread_TLS_or_heap':True,'timings_include_original_and_are_nested_nonadditive':True,'compiled':False,'game_threads_tested':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);a=p.parse_args();print(json.dumps(main(a.before),ensure_ascii=False,indent=2))
