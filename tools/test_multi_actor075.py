"""075非编译回归：解释实际C++起手条件并对照旧源码；不模拟AI线程、GPU或游戏实测。"""
from pathlib import Path
from types import SimpleNamespace as NS
import argparse,itertools,json,math,re
from test_native_melee072 import Branches,tree_sitter,tree_sitter_cpp
ROOT=Path(__file__).resolve().parents[1]

class Conditions(Branches):
    def __init__(self,source):
        self.source=source.encode('utf-8')
        self.tree=tree_sitter.Parser(tree_sitter.Language(tree_sitter_cpp.language())).parse(self.source)
        assert not self.tree.root_node.has_error
        self.functions={};self.publish=[]
        def visit(node):
            if node.type=='function_definition':
                body=node.child_by_field_name('body');head=self.source[node.start_byte:body.start_byte].decode('utf-8')
                for name in ('Choose','PickRanged','Tick'):
                    if re.search(r'\b'+name+r'\s*\(',head):self.functions[name]=body
            if node.type=='call_expression':
                fn=node.child_by_field_name('function')
                if self.txt(fn)=='IrisRanged::Publish':self.publish.append(node.child_by_field_name('arguments').named_children[1])
            for child in node.named_children:visit(child)
        visit(self.tree.root_node)
        assert len(self.functions)==3 and len(self.publish)==1
    def expr(self,node,e):
        # 只为旧全局名额反例补充比较操作；实际新条件与072共用同一表达式解释器。
        if node.type=='binary_expression':
            left=node.child_by_field_name('left');right=node.child_by_field_name('right');op=self.source[left.end_byte:right.start_byte].decode().strip()
            if op in ('<','>='):
                a=self.expr(left,e);b=self.expr(right,e)
                return a<b if op=='<' else a>=b
        return super().expr(node,e)
    def passes_prefix(self,name,e):
        # 读取函数内真实早退条件，停在招式加权循环之前；不把条件解释说成执行了完整C++选招。
        for node in self.functions[name].named_children:
            if node.type=='for_statement' and 'moves[' in self.txt(node):break
            if node.type=='if_statement':
                arm=node.child_by_field_name('consequence')
                assert 'return ' in self.txt(arm),(name,self.txt(arm))
                if self.expr(node.child_by_field_name('condition'),e):return False
        return True

def environment(other_states,warm=True,ready=True,same=True,finite=True,eligible=True,tracked=True,active=False,reserved=False,paused=False,in_range=True,weapon=True):
    animation=object();actor=NS(ready=ready,animation=animation if same else object(),active=active,reserved=reserved)
    occupancy=sum(bool(a or b) for a,b in other_states)+bool(active or reserved)
    # 外部占用数量来自独立场景数据，专门检验它不应影响另一持有者；不复刻引擎动画调度。
    return {'actor':actor,'a':actor,'c':NS(animation=animation),'it':NS(second=actor) if tracked else None,
            'actors':NS(end=lambda:None),'warmReady':warm,'range':8 if finite else float('nan'),
            'Iris::ActorReady':lambda c:eligible,'Finite':math.isfinite,'active':occupancy,'activeCount':occupancy,'maxActors':1,
            'rangedWeapon':weapon,'canShoot':warm and ready,'inMoveRange':in_range,'paused':paused}

def main(before=None):
    text=(ROOT/'IrisCombat.cpp').read_text('utf-8-sig');current=Conditions(text)
    # 三个正式入口均不得读取其他Actor的起手总数，104已取消正式人数限制；查询/医疗预算仍独立保持。
    assert not re.search(r'\bmaxActors\b',re.sub(r'//[^\n]*','',text))
    scenarios=[[],[(True,False)],[(False,True)],[(True,False)]*7,[(False,True)]*7,[(True,False),(False,True),(False,False)]*2]
    cases=0
    for other,warm,ready,same,finite,eligible,tracked in itertools.product(scenarios,(False,True),(False,True),(False,True),(False,True),(False,True),(False,True)):
        e=environment(other,warm=warm,ready=ready,same=same,finite=finite,eligible=eligible,tracked=tracked)
        assert current.passes_prefix('Choose',e)==(warm and ready and same and finite and eligible and tracked)
        assert current.passes_prefix('PickRanged',e)==(warm and ready)
        cases+=2
    for other,warm,ready,active,paused,in_range,weapon in itertools.product(scenarios,(False,True),(False,True),(False,True),(False,True),(False,True),(False,True)):
        e=environment(other,warm=warm,ready=ready,active=active,paused=paused,in_range=in_range,weapon=weapon)
        assert bool(current.expr(current.publish[0],e))==(weapon and warm and ready and in_range and not paused and not active)
        cases+=1
    # 2/3/8/9/16/32人同窗口已有其他持有者预留后，后续角色仍通过自身起手门；其自身active继续关闭远程就绪。
    groups=[]
    for count in (2,3,8,9,16,32):
        for name in ('Choose','PickRanged','Publish'):
            accepted=[]
            for actor_index in range(count):
                e=environment([(False,True)]*actor_index)
                allow=current.expr(current.publish[0],e) if name=='Publish' else current.passes_prefix(name,e)
                assert allow;accepted.append(actor_index)
            groups.append({'path':name,'holders':count,'accepted_prefixes':accepted})
    regressions=[]
    if before:
        old=Conditions(Path(before).read_text('utf-8-sig'));e=environment([(True,False),(False,True)])
        for name in ('Choose','PickRanged','Publish'):
            previous=old.expr(old.publish[0],e) if name=='Publish' else old.passes_prefix(name,e)
            after=current.expr(current.publish[0],e) if name=='Publish' else current.passes_prefix(name,e)
            assert not previous and after
            regressions.append({'path':name,'other_holders':2,'before':bool(previous),'after':bool(after)})
    # 实际医疗/原生候选门仍解释072源码执行，覆盖缺臂、义肢由原生标志维护等既有资格边界。
    from test_native_melee072 import main as native_checks
    native=native_checks()
    return {'actual_CPP_condition_cases':cases,'same_window_groups':groups,'old_source_negative_controls':regressions,
            'native_eligibility_cases':native['source_branch_cases'],'model_boundary':'actual AST conditions with engine values mocked; weighted loops and engine not executed',
            'formal_holder_limit':None,'compiled':False,'game_tested':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--baseline',type=Path);args=parser.parse_args()
    print(json.dumps(main(args.baseline),ensure_ascii=False,indent=2))
