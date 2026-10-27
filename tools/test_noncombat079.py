"""079非编译回归：执行实际C++分支AST；验证空手工作与原生拔枪阶段。
不执行游戏、C++或线程，不把脚本解释当作实机工作进度验证。
"""
from pathlib import Path
from types import SimpleNamespace as NS
import argparse,itertools,json,re
from test_native_melee072 import Branches,Returned,tree_sitter,tree_sitter_cpp
ROOT=Path(__file__).resolve().parents[1]
class Execute(Branches):
 def __init__(self,text):
  self.source=re.sub(r'\b__fastcall\b','',text).encode();self.tree=tree_sitter.Parser(tree_sitter.Language(tree_sitter_cpp.language())).parse(self.source);assert not self.tree.root_node.has_error
  self.functions={};self.locks=0;self.draw_condition=None
  def visit(n):
   if n.type=='function_definition':
    b=n.child_by_field_name('body');head=self.source[n.start_byte:b.start_byte].decode()
    for name in ('Held','Equipping','UseHook','HasHook','GunHook'):
     if re.search(r'\b'+name+r'\s*\(',head):self.functions[name]=b
   if n.type=='if_statement':
    arm=n.child_by_field_name('consequence')
    if arm and self.txt(arm).startswith('c->drawWeapon(item,item->inventorySection)'):self.draw_condition=n.child_by_field_name('condition')
   for child in n.named_children:visit(child)
  visit(self.tree.root_node)
 def expr(self,n,e):
  if n.type=='string_literal':return json.loads(self.txt(n))
  return super().expr(n,e)
 def statement(self,n,e):
  if n.type=='declaration' and self.txt(n).startswith('Guard lock'):self.locks+=1;return
  if n.type=='expression_statement':
   if n.named_children:self.expr(n.named_children[0],e)
   return
  return super().statement(n,e)

def main(before):
 source=(ROOT/'IrisRanged.cpp').read_text('utf8');oldsource=before.read_text('utf8');now=Execute(source);old=Execute(oldsource);trace=[];private=object();nativegun=object();slot=NS(published=True,gun=private)
 def weapon(identity):return None if identity is None else NS(getGameData=lambda:None if identity=='missing_data' else NS(stringID=identity))
 def make_env(eligible,identity,published,found,native_has):
  owner=NS(getCurrentWeapon=lambda:weapon(identity));slot.published=published
  def discover(c):trace.append(('discover',c))
  def has(*args):trace.append(('native_has',args));return native_has
  def gun(*args):trace.append(('native_gun',args));return nativegun
  env={'c':owner,'ai':NS(me=owner),'ranged':NS(me=owner),'target':object(),'pos':object(),'Eligible':lambda c:eligible,'Find':lambda c:slot if found else None,'Discover':discover,'originalHas':has,'originalGun':gun,'originalUse':lambda c:False}
  env['Held']=lambda c:now.run('Held',dict(env,c=c));return env
 cases=0
 for eligible,identity,published,found,native_has in itertools.product((False,True),(None,'1-IrisArsenal.mod','sword','crossbow','missing_data'),(False,True),(False,True),(False,True)):
  env=make_env(eligible,identity,published,found,native_has);is_held=identity=='1-IrisArsenal.mod'
  trace.clear();result=now.run('HasHook',env);expected=bool(found and published) if eligible and is_held else native_has
  assert bool(result)==expected,(identity,result,expected)
  calls=[x for x in trace if x[0]=='native_has'];assert len(calls)==(0 if eligible and is_held else 1)
  if calls:assert calls[0][1]==(env['ai'],env['target'],env['pos'])
  trace.clear();result=now.run('GunHook',env);expected=private if eligible and is_held and found and published else 0 if eligible and is_held else nativegun
  assert result is expected or result==expected
  calls=[x for x in trace if x[0]=='native_gun'];assert len(calls)==(0 if eligible and is_held else 1)
  if calls:assert calls[0][1]==(env['ranged'],)
  # 库存能力入口保持旧语义；收起不影响能力发现/选招评分。
  assert bool(now.run('UseHook',env))==bool(old.run('UseHook',env));cases+=3
 # 旧代码反例：远程开、槽就绪、双手已空时仍报告持弩；经hasAnythingEquipped的OR传播。
 env=make_env(True,None,True,True,False);assert old.run('HasHook',env) is True;assert now.run('HasHook',env) is False
 native_melee_equipped=False;assert (bool(now.run('HasHook',env)) or native_melee_equipped) is False
 # 反复收起/拔出只改变真实手持谓词，不删除能力、不改远程开关。
 sequence=[None,'1-IrisArsenal.mod',None,'1-IrisArsenal.mod',None]
 assert [bool(now.run('HasHook',make_env(True,x,True,True,False))) for x in sequence]==[False,True,False,True,False]
 assert now.run('Held',{'c':None}) is False
 equip_cases=0
 for key in (None,264,265,87,152,263,267):
  task=None if key is None else NS(key=lambda:key);owner=NS(getBody=lambda:NS(getCurrentAction=lambda:task))
  eq=now.run('Equipping',{'c':owner,'EQUIP_CROSSBOW':264});assert bool(eq)==(key==264)
  for mode,held,has_item in itertools.product((False,True),repeat=3):
   item=object() if has_item else None;owner.rangedCombat=NS(combatMode=mode);owner.getCurrentWeapon=lambda:item if held else None
   actual=now.expr(now.draw_condition,{'c':owner,'item':item,'equipping':eq});assert bool(actual)==bool(has_item and (mode or key==264) and not held);equip_cases+=1
 assert now.run('Equipping',{'c':None,'EQUIP_CROSSBOW':264}) is False
 assert now.run('Equipping',{'c':NS(getBody=lambda:None),'EQUIP_CROSSBOW':264}) is False
 # 资格、瞄准、动画、防御/结算等原函数保持逐字；只准两个状态Hook和Prepare拔枪条件改变。
 from test_hook_audit078 import business_tokens,HOOKS
 unchanged=[n for n in HOOKS['IrisRanged.cpp'] if n not in ('HasHook','GunHook')]
 assert business_tokens(source,unchanged)==business_tokens(oldsource,unchanged)
 def region(text,a,b):return text[text.index(a):text.index(b)]
 assert region(source,'bool Eligible(','// 构造/销毁')==region(oldsource,'bool Eligible(','// 构造/销毁')
 assert region(source,'bool CaptureAim(','bool TakeRequest(')==region(oldsource,'bool CaptureAim(','bool TakeRequest(')
 assert source.count('KenshiLib::AddHook(')==oldsource.count('KenshiLib::AddHook(')==8
 assert all(x not in source for x in ('CreateThread(','GetAsyncKeyState(','WriteProcessMemory('))
 # SDK声明及实际链接库符号存在；不把它当类型检查或成功链接。
 deps=Path('E:/KenshiProject/1.Dependencies/KenshiLib_0.5.0');lib=(deps/'Libraries/KenshiLib.lib').read_bytes()
 for file,symbol in [('Character.h','getBody'),('CharBody.h','getCurrentAction'),('Tasker.h','key')]:
  assert symbol+'(' in (deps/'Include/kenshi'/file).read_text('utf8');assert (symbol+'@').encode() in lib
 return {'actual_AST_hook_cases':cases,'actual_AST_draw_predicate_cases':equip_cases,'old_false_equipped_counterexample_detected':True,'native_parameters_and_once_forwarding':True,'ability_unchanged':True,'unchanged_other_ranged_hooks':unchanged,'SDK_and_library_symbols':3,'new_hooks':0,'new_threads':0,'compiled':False,'game_work_progress_measured':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--before-ranged',type=Path,required=True);a=p.parse_args();print(json.dumps(main(a.before_ranged),ensure_ascii=False,indent=2))
