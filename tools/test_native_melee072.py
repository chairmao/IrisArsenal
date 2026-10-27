"""072非编译回归：解释实际C++选招分支，模拟原生返回/医疗状态；不模拟游戏医疗计算。"""
from pathlib import Path
from types import SimpleNamespace as NS
import itertools,json,re,sys
ROOT=Path(__file__).resolve().parents[1]
# 沿用已安装的语法依赖；只解释本次函数的语法树，不执行C++、预处理、编译或链接。
DEP=Path('D:/CodexWorkSpace/Sessions/20261002-235652-kenshi-crash-407794f2/Task-IrisArsenal-EightMoves-20261016-012351-58b640/tools/syntax')
sys.path.insert(0,str(DEP))
import tree_sitter,tree_sitter_cpp

class Returned(Exception):
    def __init__(self,value):self.value=value

class Branches:
    def __init__(self):
        self.source=re.sub(r'\b__fastcall\b','', (ROOT/'IrisArsenal.cpp').read_text('utf-8-sig')).encode('utf-8')
        self.tree=tree_sitter.Parser(tree_sitter.Language(tree_sitter_cpp.language())).parse(self.source)
        assert not self.tree.root_node.has_error
        self.functions={}
        def visit(n):
            if n.type=='function_definition':
                body=n.child_by_field_name('body');head=self.source[n.start_byte:body.start_byte].decode('utf8')
                for name in ('NativeStandingMeleeAllowed','ChooseHook'):
                    if re.search(r'\b'+name+r'\s*\(',head):self.functions[name]=body
            for child in n.named_children:visit(child)
        visit(self.tree.root_node);assert len(self.functions)==2
    def txt(self,n):return self.source[n.start_byte:n.end_byte].decode('utf8')
    def expr(self,n,e):
        kind=n.type
        if kind in ('identifier','qualified_identifier'):return e[self.txt(n)]
        if kind=='number_literal':return float(self.txt(n)) if '.' in self.txt(n) else int(self.txt(n))
        if kind in ('true','false'):return kind=='true'
        if kind in ('condition_clause','parenthesized_expression'):return self.expr(n.named_children[0],e)
        if kind=='field_expression':return getattr(self.expr(n.child_by_field_name('argument'),e),self.txt(n.child_by_field_name('field')))
        if kind=='call_expression':
            fn=self.expr(n.child_by_field_name('function'),e)
            return fn(*[self.expr(a,e) for a in n.child_by_field_name('arguments').named_children])
        if kind in ('unary_expression','pointer_expression'):
            arg=n.child_by_field_name('argument') or n.named_children[-1];v=self.expr(arg,e);op=self.source[n.start_byte:arg.start_byte].decode().strip()
            if op=='!':return not v
            if op=='&':return v
            raise AssertionError((kind,op))
        if kind=='binary_expression':
            left=n.child_by_field_name('left');right=n.child_by_field_name('right');op=self.source[left.end_byte:right.start_byte].decode().strip();a=self.expr(left,e)
            if op=='&&':return bool(a) and bool(self.expr(right,e))
            if op=='||':return bool(a) or bool(self.expr(right,e))
            b=self.expr(right,e)
            if op=='!=':return a!=b
            if op=='==':return a==b
            raise AssertionError(op)
        if kind=='conditional_expression':return self.expr(n.child_by_field_name('consequence') if self.expr(n.child_by_field_name('condition'),e) else n.child_by_field_name('alternative'),e)
        raise AssertionError((kind,self.txt(n)))
    def statement(self,n,e):
        if n.type=='comment':return
        if n.type=='compound_statement':
            for child in n.named_children:self.statement(child,e)
        elif n.type=='if_statement':
            arm='consequence' if self.expr(n.child_by_field_name('condition'),e) else 'alternative'
            child=n.child_by_field_name(arm)
            if child:self.statement(child,e)
        elif n.type=='return_statement':raise Returned(self.expr(n.named_children[0],e) if n.named_children else None)
        elif n.type=='declaration':
            # Lock lock仅表示既有互斥域；测试不声称模拟了引擎线程或实际锁调度。
            # 076新增审计及带参数锁仅代表互斥/观察域；不在此假装模拟线程调度。
            if self.txt(n).startswith(('Lock lock','IrisDiagnostics::HookAudit audit')):e['lock']=None;return
            for child in n.named_children:
                if child.type=='init_declarator':
                    name=re.findall(r'[A-Za-z_]\w*',self.txt(child.child_by_field_name('declarator')))[-1]
                    e[name]=self.expr(child.child_by_field_name('value'),e)
        else:raise AssertionError((n.type,self.txt(n)))
    def run(self,name,e):
        local=dict(e)
        try:self.statement(self.functions[name],local)
        except Returned as r:return r.value
        raise AssertionError('未执行return：'+name)

HEAVY,UNARMED,OTHER,NORMAL=3,5,0,0
class Technique:
    def __init__(self,skills,prone=False):self.skills=set(skills);self.isProne=prone
    def hasSkillType(self,kind):return kind in self.skills

def main():
    interpreter=Branches();calls=[];native_kind='weapon';selected=object()
    original_types={'weapon':Technique([HEAVY]),'unarmed':Technique([UNARMED]),'prone':Technique([HEAVY],True),'other':Technique([OTHER]),'mixed':Technique([HEAVY,UNARMED]),'empty':None}
    def case(left=True,right=True,prone=0,crippled=False,ready=True,category=HEAVY,native_kind='weapon',range=8,selection=True,enabled=True,running=1,faulted=False,uses=True):
        native=original_types[native_kind];trace=[]
        medical=NS(isCrippled=lambda:crippled,isLeftArmOk=lambda:left,isRightArmOk=lambda:right)
        actor=NS(medical=medical,getProneState=lambda:prone,ready=ready)
        stats=NS(me=actor,currentWeaponType=category)
        def original(*args):trace.append(('native',args));return native
        def choose(*args):trace.append(('private',args));return selected if selection else None
        e={'stats':stats,'range':range,'reach':18,'last':object(),'stationary':False,'running':running,'enabled':enabled,'faulted':faulted,'originalChoose':original,'InterlockedCompareExchange':lambda old,x,c:old,'UsesWeapon':lambda s:uses,'ActorReady':lambda c:bool(c and c.ready),'SKILL_HEAVY':HEAVY,'SKILL_UNARMED':UNARMED,'PS_NORMAL':NORMAL,'IrisCombat::ProofOnly':lambda:False,'IrisCombat::Choose':choose}
        e['NativeStandingMeleeAllowed']=lambda stats,native:interpreter.run('NativeStandingMeleeAllowed',dict(e,stats=stats,native=native))
        result=interpreter.run('ChooseHook',e)
        assert trace[0][0]=='native' and sum(x[0]=='native' for x in trace)==1
        assert trace[0][1]==(stats,range,18,e['last'],False),'原生参数不得变更'
        calls.append({'native_kind':native_kind,'left':left,'right':right,'prone':prone,'crippled':crippled,'ready':ready,'category':category,'range':range,'private_calls':sum(x[0]=='private' for x in trace),'returned':'private' if result is selected else 'native'})
        return result,native,trace
    # 独立需求矩阵：双臂/五种原生姿态/残疾标志/当前类别/原生候选，检查真实源码分支。
    count=0
    for left,right,prone,crippled,category,kind in itertools.product((False,True),(False,True),range(5),(False,True),(HEAVY,UNARMED,OTHER),original_types):
        result,native,trace=case(left=left,right=right,prone=prone,crippled=crippled,category=category,native_kind=kind)
        # 076玩家要求类别随FCS；武术、趴地、混合武术和不匹配类别仍保留原生。
        allowed=left and right and prone==NORMAL and not crippled and category!=UNARMED and (kind=='empty' or (not native.isProne and native.hasSkillType(category) and not native.hasSkillType(UNARMED)))
        assert (result is selected)==allowed,(left,right,prone,crippled,category,kind)
        assert (sum(x[0]=='private' for x in trace)==1)==allowed
        if not allowed:assert result is native
        count+=1
    for kwargs in ({'ready':False},{'enabled':False},{'running':0},{'faulted':True},{'uses':False},{'selection':False},{'selection':False,'native_kind':'empty'}):
        result,native,trace=case(**kwargs);assert result is native
    # 原生为空不封专属远距；这里模拟选择器返回已合法的候选，不冒充测试了真实引擎距离计算。
    for distance in (0,18,50,80):assert case(native_kind='empty',range=distance)[0] is selected
    assert case(native_kind='weapon',selection=False)[0] is original_types['weapon']
    # 空actor由短路保护，不能解引用后续医疗/武器字段。
    assert interpreter.run('NativeStandingMeleeAllowed',{'stats':None,'native':None,'ActorReady':lambda c:False,'SKILL_HEAVY':HEAVY,'SKILL_UNARMED':UNARMED,'PS_NORMAL':NORMAL}) is False
    # 直接检查实际私选的距离比较仍在，新的资格检查没有改写其min/max或权重。
    combat=(ROOT/'IrisCombat.cpp').read_text('utf-8-sig')
    assert 'range>=t->minDistanceVsStatic&&range<=t->initialDistance' in combat
    from stage_package import validate_dll,MELEE_CONTRACT
    dll=(ROOT.parent/'bin/Release/IrisArsenal.dll').read_bytes();dll_status='existing contract present'
    if MELEE_CONTRACT.encode('ascii') not in dll:
        try:validate_dll()
        except RuntimeError as error:assert '072原生近战资格与回退' in str(error);dll_status='actual old DLL rejected'
        else:raise AssertionError('旧DLL未被拒绝')
    return {'source_branch_cases':len(calls),'matrix_cases':count,'original_called_once_and_arguments_preserved':True,'native_null_can_reach_private_ranges':[0,18,50,80],'private_failure_preserves_native':True,'existing_dll':dll_status,'validation':'actual C++ AST interpreted with mocked engine calls','native_injury_state_transition_tested':False,'compiled':False,'game_tested':False}

if __name__=='__main__':print(json.dumps(main(),ensure_ascii=False,indent=2))
