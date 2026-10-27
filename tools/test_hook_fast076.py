"""076非编译回归：解释真实Hook语法树与075原件对照；不执行C++或假称线程/游戏实测。"""
from pathlib import Path
from types import SimpleNamespace as NS
import argparse,itertools,json,re,random
from test_native_melee072 import Branches,Returned,tree_sitter,tree_sitter_cpp
ROOT=Path(__file__).resolve().parents[1]
class MockFailure(Exception):pass
class Execute(Branches):
    def __init__(self,text):
        text=re.sub(r'__declspec\(align\(64\)\)','',text)
        self.source=re.sub(r'\b__fastcall\b','',text).encode();self.tree=tree_sitter.Parser(tree_sitter.Language(tree_sitter_cpp.language())).parse(self.source)
        assert not self.tree.root_node.has_error
        self.functions={};self.locks=0
        def walk(n):
            if n.type=='function_definition':
                body=n.child_by_field_name('body');head=self.source[n.start_byte:body.start_byte].decode()
                for name in ('StartHook','RunHook','MeleeBlockCheckHook','MeleeStumbleHook','MayNeedTechniqueGuard','ChooseHook','NativeStandingMeleeAllowed','BeforeLock','Acquired','BeforeUnlock','HookSummary'):
                    if re.search(r'\b'+name+r'\s*\(',head):self.functions[name]=body
            for c in n.named_children:walk(c)
        walk(self.tree.root_node)
    def expr(self,n,e):
        if n.type=='argument_list':return [self.expr(x,e) for x in n.named_children]
        if n.type=='subscript_expression':return self.expr(n.child_by_field_name('argument'),e)[self.expr(n.child_by_field_name('indices').named_children[0],e)]
        if n.type=='binary_expression':
            a=n.child_by_field_name('left');b=n.child_by_field_name('right');op=self.source[a.end_byte:b.start_byte].decode().strip()
            if op=='>=':return self.expr(a,e)>=self.expr(b,e)
            if op=='<':return self.expr(a,e)<self.expr(b,e)
        if n.type in ('assignment_expression','update_expression'):
            target=n.child_by_field_name('left') or n.child_by_field_name('argument') or n.named_children[0]
            value=self.expr(n.child_by_field_name('right'),e) if n.type=='assignment_expression' else self.expr(target,e)+1
            if target.type=='identifier':e[self.txt(target)]=value
            elif target.type=='field_expression':setattr(self.expr(target.child_by_field_name('argument'),e),self.txt(target.child_by_field_name('field')),value)
            else:raise AssertionError(self.txt(n))
            return value
        return super().expr(n,e)
    def statement(self,n,e):
        if n.type=='declaration' and self.txt(n).startswith(('Lock lock','Guard guard')):self.locks+=1;return
        if n.type=='declaration' and self.txt(n).startswith('IrisDiagnostics::HookAudit audit'):e['audit']=None;return
        if n.type=='expression_statement':
            if n.named_children:self.expr(n.named_children[0],e)
            return
        if n.type=='for_statement':
            # 仅本轮未改的原型空演员表分支；不模拟地图迭代或原型实际演出。
            init=n.child_by_field_name('initializer');self.statement(init,e)
            assert not self.expr(n.child_by_field_name('condition'),e),'测试不执行原型非空Actor循环'
            return
        if n.type=='try_statement':
            body=n.child_by_field_name('body') or next(c for c in n.named_children if c.type=='compound_statement')
            try:self.statement(body,e)
            except MockFailure:
                catch=next(c for c in n.named_children if c.type=='catch_clause')
                self.statement(catch.child_by_field_name('body') or catch.named_children[-1],e)
            return
        return super().statement(n,e)
    def run(self,name,e):
        local=dict(e)
        try:self.statement(self.functions[name],local)
        except Returned as r:return r.value
        return None

def main(before_root):
    olda=Execute((before_root/'IrisArsenal.cpp').read_text('utf-8-sig'));newa=Execute((ROOT/'IrisArsenal.cpp').read_text('utf-8-sig'))
    oldc=Execute((before_root/'IrisCombat.cpp').read_text('utf-8-sig'));newc=Execute((ROOT/'IrisCombat.cpp').read_text('utf-8-sig'))
    own,remote,proof,ordinary=object(),object(),object(),object();owned=(own,remote,proof);cases=0;fast=0
    actor=NS(stumbles=0);animation=object();trace=[]
    def original(*args):trace.append(('native',args));return 73
    for name,t,running in itertools.product(('StartHook','RunHook'),(own,remote,proof,ordinary,None),(0,1)):
        def speed(*args):return 2*args[2] if running and args[1] in owned else args[2]
        env={'a':animation,'t':t,'speed':1.25,'extra':'原生参数','technique':proof,'running':running,'originalStart':original,'originalRun':original,'Speed':speed,
             'InterlockedCompareExchange':lambda v,x,c:v,'IrisCombat::OwnTechniqueIdentity':lambda x:x in owned,'IrisCombat::Started':lambda *x:None,'actors':NS(begin=lambda:None,end=lambda:None)}
        outputs=[]
        for machine in (olda,newa):
            trace.clear();machine.locks=0;machine.run(name,env);outputs.append((list(trace),machine.locks))
        assert outputs[0][0]==outputs[1][0] and len(outputs[1][0])==1,(name,t,running,outputs)
        if t is ordinary:assert outputs[1][1]==0;fast+=1
        cases+=1
    choose_cases=0;choose_fast=0
    # 原生返回、配置、故障和实际武器身份交叉；角色是否玩家不是入口条件。
    for uses,running,enabled,faulted,medical,private_available,native in itertools.product((False,True),(0,1),(False,True),(False,True),(False,True),(False,True),(None,ordinary)):
        stats=NS(me=actor,currentWeaponType=0)
        env={'stats':stats,'range':31,'reach':17,'last':ordinary,'stationary':True,'running':running,'enabled':enabled,'faulted':faulted,
             'InterlockedCompareExchange':lambda v,x,c:v,'UsesWeapon':lambda s:uses,'IrisCombat::ProofOnly':lambda:False,
             'NativeStandingMeleeAllowed':lambda *args:medical,'IrisCombat::Choose':lambda *args:own if private_available else None}
        def choose_original(*args):trace.append(('native',args));return native
        env['originalChoose']=choose_original;outputs=[]
        for machine in (olda,newa):
            trace.clear();machine.locks=0;result=machine.run('ChooseHook',env);outputs.append((result,list(trace),machine.locks))
        assert outputs[0][:2]==outputs[1][:2] and len(outputs[1][1])==1
        assert outputs[1][1][0][1]==(stats,31,17,ordinary,True)
        if not uses:assert outputs[1][2]==0;choose_fast+=1
        choose_cases+=1
    dynamic_cases=0
    for category,kind,left,right in itertools.product(range(9),('matching','empty','unarmed_mix','prone','wrong'),(False,True),(False,True)):
        native=None if kind=='empty' else NS(isProne=kind=='prone',hasSkillType=lambda n:n==(category+1)%9 if kind=='wrong' else (n==category or (kind=='unarmed_mix' and n==5)))
        actor=NS(medical=NS(isCrippled=lambda:False,isLeftArmOk=lambda:left,isRightArmOk=lambda:right),getProneState=lambda:0)
        env={'stats':NS(me=actor,currentWeaponType=category),'native':native,'ActorReady':lambda a:True,'SKILL_UNARMED':5,'PS_NORMAL':0}
        result=newa.run('NativeStandingMeleeAllowed',env)
        assert result==bool(left and right and category!=5 and kind in ('matching','empty')),(category,kind,left,right)
        dynamic_cases+=1
    actor=NS(stumbles=0)
    # 近战当前技巧和远程动画要求交叉组合，含无角色、失效保护、开关关闭、异常转原生。
    for current,required,valid,enabled,fail in itertools.product((None,ordinary,own,remote),(None,ordinary,own,remote),(False,True),(False,True),(False,True)):
        combat=NS(getCurrentTechnique=lambda:current);owner=NS(animation=NS(animationRequirements=NS(_currentCombatTechnique=required)),handle='owner',isValid=lambda:True,isDestroyed=lambda:False)
        combat.me=owner;owner.getCombatClass=lambda:combat
        combat._getHit=lambda *args:trace.append(('getHit',args))
        def protected_melee(c):
            if fail:raise MockFailure()
            return 0 if valid and current is own else -1
        def protected_ranged(c):return 5 if valid and required is remote else -1
        def find(h):return NS(second=actor)
        moves=[NS(immuneReactions=enabled,preventBlock=enabled) for _ in range(10)]
        damage=NS(cut=1,blunt=2,pierce=0,extraStun=0)
        env={'self':combat,'myAttack':2,'incomingAttack':3,'dir':0,'damage':damage,'part':None,'attacker':None,
             'originalBlockCheck':original,'originalMeleeStumble':original,'ProtectedMeleeMove':protected_melee,'ProtectedRangedMove':protected_ranged,
             'moves':moves,'Finite':lambda v:True,'actors':NS(find=find),'IrisDiagnostics::DetailsEnabled':lambda:False,
             'IrisCombat::OwnTechniqueIdentity':lambda x:x in owned,'OwnTechniqueIdentity':lambda x:x in owned}
        env['MayNeedTechniqueGuard']=lambda c,r:newc.run('MayNeedTechniqueGuard',dict(env,combat=c,includeRanged=r))
        for name in ('MeleeBlockCheckHook','MeleeStumbleHook'):
            env['self']=owner if name=='MeleeStumbleHook' else combat
            may=current in owned or (name=='MeleeStumbleHook' and required in owned)
            if fail and not may:continue # 仅在原保护检查会被调用的候选内注入标准异常。
            outputs=[]
            for machine in (oldc,newc):
                trace.clear();actor.stumbles=0;machine.locks=0;result=machine.run(name,env);outputs.append((result,list(trace),actor.stumbles,machine.locks))
            assert outputs[0][:3]==outputs[1][:3],(name,current,required,valid,enabled,outputs)
            may=current in owned or (name=='MeleeStumbleHook' and required in owned)
            if not may:assert outputs[1][3]==0 and outputs[0][3]==1;fast+=1
            cases+=1
    # 负向对照：若遗漏远程动画要求预筛，则实际Ranged保护会被误拒绝，必须被比较器发现。
    broken=Execute((ROOT/'IrisCombat.cpp').read_text('utf8').replace('return animation&&OwnTechniqueIdentity(animation->animationRequirements._currentCombatTechnique);','return false;'))
    testcombat=NS(getCurrentTechnique=lambda:ordinary,me=NS(animation=NS(animationRequirements=NS(_currentCombatTechnique=remote)),isValid=lambda:True,isDestroyed=lambda:False))
    probe={'combat':testcombat,'includeRanged':True,'OwnTechniqueIdentity':lambda t:t in owned}
    assert newc.run('MayNeedTechniqueGuard',probe) is True and broken.run('MayNeedTechniqueGuard',probe) is False
    # 未知预筛情况回旧路：标准异常不得被误当“不属于本模组”。
    testcombat.getCurrentTechnique=lambda:(_ for _ in ()).throw(MockFailure())
    assert newc.run('MayNeedTechniqueGuard',probe) is True
    testcombat.getCurrentTechnique=lambda:ordinary
    testcombat.me=NS(isValid=lambda:False,isDestroyed=lambda:True)
    assert newc.run('MayNeedTechniqueGuard',probe) is False # 不提供animation，若错误读取立即失败。
    assert newc.run('MayNeedTechniqueGuard',dict(probe,combat=None)) is False
    # 固定快照的发布交错规格：填充过程中只读旧快照，发布后只读新快照，历史快照永不覆盖。
    schedules=0;rng=random.Random(76)
    for _ in range(64):
        order=list(range(11));rng.shuffle(order);published=None;history=[];expected={}
        for slot in order:
            old=published;new=list(old) if old else [None]*11;token=object()
            for index in range(11):
                new[index]=token if index==slot else (old[index] if old else None)
                assert published is old
                for saved,data in history:assert tuple(saved)==data
                schedules+=1
            published=tuple(new);expected[slot]=token;history.append((published,tuple(published)))
            assert all(published[k] is v for k,v in expected.items())
    code=(ROOT/'IrisCombat.cpp').read_text('utf8');arsenal=(ROOT/'IrisArsenal.cpp').read_text('utf8');diag=(ROOT/'IrisDiagnostics.cpp').read_text('utf8')
    assert 'PublishTechniqueIdentity(i,t);moves[i].technique=t;' in code
    assert code.index('next->item[i]=')<code.index('InterlockedExchangePointer(&publishedIdentities,next)')
    assert 'identityVersions>=MOVE_COUNT+1' in code and 'old&&old->item[slot]' in code
    assert 'if(!UsesWeapon(stats))return native;' in arsenal
    assert 'SKILL_HEAVY' not in re.sub(r'//[^\n]*','',arsenal)
    assert 'hooks_ready' in arsenal and 'IRIS_HOOK_FAST_076' in arsenal
    # 对真实审计方法的关闭路径解释执行：不提供QPC或原子函数，若误调用就直接失败。
    audit=Execute(diag)
    for method in ('BeforeLock','Acquired','BeforeUnlock'):
        audit.run(method,{'active':False,'sampled':False})
    audit.run('HookSummary',{'hookAuditEnabled':False})
    assert 'hookAuditEnabled=false' in diag and 'if(!active)return;' in diag
    assert 'EnterCriticalSection' not in diag[diag.index('HookAudit::HookAudit'):diag.index('static void HookSummary')]
    # 诊断关闭路径在任何原子统计/QPC之前返回；统计字段均为固定原子累计，不跨线程清零。
    assert 'active(hookAuditEnabled&&PerformanceEnabled())' in diag
    return {'actual_hook_AST_cases':cases,'choose_AST_cases':choose_cases,'non_weapon_zero_lock_cases':choose_fast,'dynamic_FCS_category_cases':dynamic_cases,'disabled_audit_methods_no_clock_or_atomics':True,'ordinary_zero_lock_routes':fast,'snapshot_interleaving_observations':schedules,'hooks_native_results_and_arguments_equal':True,'player_NPC_filter_added':False,'hardcoded_heavy_filter_added':False,'missing_ranged_identity_negative_control':True,'prefilter_exception_falls_back':True,'compiled':False,'game_tested':False,'boundary':'AST解释+模拟原生子调用及不可变发布规格；不是C++并发执行'}
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--before',type=Path,required=True);args=parser.parse_args()
    print(json.dumps(main(args.before),ensure_ascii=False,indent=2))
