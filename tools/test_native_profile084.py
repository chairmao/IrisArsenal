"""084非编译验收：实际C++ AST、原流程逐token比较及独立生命周期规格，不运行引擎。"""
from pathlib import Path
from types import SimpleNamespace as NS
import argparse,ast,configparser,hashlib,itertools,json,math,random,re,sys
ROOT=Path(__file__).resolve().parents[1] if Path(__file__).parent.name=='tools' else Path('E:/KenshiProject/2.Projects/IrisArsenal')
sys.path.insert(0,str(ROOT/'tools'))
from test_performance080 import Program,Returned
from test_medical_gate083 import condition_case,replay,function_map,tokens,ready_cases

def body_tokens(text):
    # 待比较输入已含完整函数体大括号，不能再额外包一层产生假差异。
    p=Program("void Check()"+text);return p.tokens(p.body("Check"))

class Eval(Program):
    def expr(self,n,e):
        if n.type=="assignment_expression":
            left=n.child_by_field_name("left");right=n.child_by_field_name("right")
            if left.type=="field_expression" and self.txt(left.child_by_field_name("field"))=="top":
                # top/previous是借用指针；测试解释器必须保留身份，不能按容器值深拷贝。
                value=self.expr(right,e);self.assign(left,e,value);return value
        if n.type=='binary_expression':
            l=n.child_by_field_name('left');r=n.child_by_field_name('right');op=self.source[l.end_byte:r.start_byte].decode().strip()
            if op in ('+','-','*','/','%'):
                a,b=self.expr(l,e),self.expr(r,e)
                return {'+':lambda:a+b,'-':lambda:a-b,'*':lambda:a*b,'/':lambda:a//b if isinstance(a,int) and isinstance(b,int) else a/b,'%':lambda:a%b}[op]()
        if n.type=='unary_expression' and self.txt(n).startswith('-'):return -self.expr(n.named_children[-1],e)
        return super().expr(n,e)
    def assign(self,n,e,v):
        if n.type=='subscript_expression':
            self.expr(n.child_by_field_name('argument'),e)[self.expr(n.child_by_field_name('indices').named_children[0],e)]=v
        else:super().assign(n,e,v)
    def statement(self,n,e):
        if n.type=='while_statement':
            guard=0
            while self.expr(n.child_by_field_name('condition'),e):
                self.statement(n.child_by_field_name('body'),e);guard+=1;assert guard<10000
            return
        if n.type=='for_statement':
            init=n.child_by_field_name('initializer');cond=n.child_by_field_name('condition');update=n.child_by_field_name('update')
            if init:self.statement(init,e)
            guard=0
            while not cond or self.expr(cond,e):
                self.statement(n.child_by_field_name('body'),e)
                if update:self.expr(update,e)
                guard+=1;assert guard<10000
            return
        return super().statement(n,e)

def free_body(p,name):
    found=[n.child_by_field_name("body") for n in p.nodes("function_definition") if re.search(r"\b(?:bool|void|double)\s+"+re.escape(name)+r"\s*\(",p.source[n.start_byte:n.child_by_field_name("body").start_byte].decode())]
    assert len(found)==1,(name,len(found));return found[0]

def definitions(p,name,destructor=False):
    result=[]
    for n in p.nodes('function_definition'):
        body=n.child_by_field_name('body');header=p.source[n.start_byte:body.start_byte].decode()
        if re.search(r'(?<!\w)'+('~' if destructor else '')+re.escape(name)+r'\s*\(',header) and ('~'+name+'(' in header)==destructor:result.append(body)
    assert len(result)==1,(name,destructor,len(result));return result[0]

def preserve(before,a,c,d):
    oldc=(before/'IrisCombat.cpp').read_text('utf-8-sig');olda=(before/'IrisArsenal.cpp').read_text('utf-8-sig');oldd=(before/'IrisDiagnostics.cpp').read_text('utf-8-sig')
    # 逐token恢复本轮纯诊断语句后，与083原流程比较；不只断言几个关键字符串仍存在。
    pc,po=Program(c),Program(oldc)
    flush=pc.txt(pc.body('Flush'));flush=flush.replace('IrisNativeAudit::Hit nativeProfile(r.cast,r.event,r.move,queueSnapshot.done+1);','')
    assert body_tokens(flush)==po.tokens(po.body('Flush'))
    normalized=c
    normalized=normalized.replace('IrisNativeAudit::Reset();','')
    normalized=re.sub(r'IrisNativeAudit::PartScope nativePart\(IrisNativeAudit::(?:DEFENCE|REACTION)\);','',normalized)
    normalized=normalized.replace('IrisNativeAudit::Hit nativeProfile(r.cast,r.event,r.move,queueSnapshot.done+1);','')
    normalized=normalized.replace('IrisNativeAudit::Medical(before,after,done,inspected,reason,begin>0&&now>=begin?now-begin:0);','')
    newer,older=function_map(normalized),function_map(oldc)
    assert all(newer[key]==body for key,body in older.items())
    assert len(set(newer)-set(older))==1
    # SafeHook原生先执行、原短路检查顺序、每帧一次与Tick→Flush顺序均不动。
    sa=Program(a);soa=Program(olda);safe=sa.txt(sa.body('SafeHook'))
    inserted='originalSafe(w);if(!InterlockedCompareExchange(&running,0,0)||DWORD(InterlockedCompareExchange(&mainThread,0,0))!=GetCurrentThreadId()||frameWorld!=w)return;\n    ObserveServiceOpportunity(w,updateDone);if(updateDone)return;updateDone=true;'
    original='originalSafe(w);if(!InterlockedCompareExchange(&running,0,0)||DWORD(InterlockedCompareExchange(&mainThread,0,0))!=GetCurrentThreadId()||frameWorld!=w||updateDone)return;updateDone=true;'
    assert inserted in safe;safe=safe.replace(inserted,original)
    assert body_tokens(safe)==soa.tokens(soa.body('SafeHook'))
    frame=sa.txt(sa.body('FrameHook')).replace('IrisNativeAudit::Frame serviceFrame(realFrameToken);','').replace('serviceFrame.Finish();','')
    assert body_tokens(frame)==soa.tokens(soa.body('FrameHook'))
    for name in ('Idle','ChooseHook','NativeStandingMeleeAllowed','StartHook','RunHook','ResetHook','ShutdownHook'):
        assert sa.tokens(sa.body(name))==soa.tokens(soa.body(name)),name
    for name in ('Contacts','ResolveJobs','AdvanceEffects','CanDamage','Tick','Configure'):
        assert pc.tokens(pc.body(name))==po.tokens(po.body(name)),name
    clean=lambda s:re.sub(r"__declspec\((?:[^()]|\([^()]*\))*\)","",s)
    sd,sod=Program(clean(d)),Program(clean(oldd))
    for name in ('Record','BeginFrame','EndFrame','RecordWait','ObserveWindow','SnapshotWaits','PerformanceEnabled','DetailsEnabled','WindowAuditEnabled','WindowAuditHasWork','RecordMedicalWindow'):
        assert sd.tokens(free_body(sd,name))==sod.tokens(free_body(sod,name)),name
    return {'combat_functions_equivalent_after_observer_removal':len(older),'complete_Flush_tokens_preserved':True,'SafeHook_original_short_circuit_and_once_per_frame_preserved':True,'original_frame_clock_preserved':True}

def histogram(p):
    bound=re.search(r'bounds\[15\]=\{([^}]+)',p.source.decode());bounds=[float(x) for x in bound[1].split(',')]
    e=dict(n=0,sum=0.,max=0.,buckets=[0]*16,bounds=bounds,_finite=math.isfinite);e['std::max']=max
    vals=[-1.,float('nan'),float('inf'),0.]
    for b in bounds:vals += [b,max(0.,b-1e-8),b+1e-8]
    vals += [random.Random(84+i).random()*140 for i in range(300)]
    expected=[]
    for value in vals:
        e['ms']=value
        try:p.statement(p.body('Add'),e)
        except Returned:pass
        if math.isfinite(value) and value>=0:expected.append(value)
    assert e['n']==len(expected) and math.isclose(e['sum'],sum(expected)) and e['max']==max(expected)
    buckets=[sum(1 for x in expected if next((i for i,b in enumerate(bounds) if x<=b),15)==i) for i in range(16)]
    assert e['buckets']==buckets and sum(buckets)==len(expected)
    for percentile in (1,25,50,75,95,99,100):
        e['p']=percentile;actual=p.execute(p.body('Percent'),e)
        exact=sorted(expected)[math.ceil(len(expected)*percentile/100)-1]
        upper=next((x for x in bounds if exact<=x),-1)
        assert actual==upper,(percentile,actual,upper)
    return {'actual_Add_AST_inputs':len(vals),'actual_percentile_AST_cases':7,'negative_nonfinite_ignored':True,'basis':'per_native_root_scope_exit'}

def parts(p):
    count=0
    # 实际PartScope析构体：每个叶/嵌套/同阶段/时钟失效路径，独占量扣除子树。
    body=definitions(p,'PartScope',True)
    for part,elapsed,children,with_parent,valid in itertools.product(range(4),(0.,.05,2.5,7.65),(0.,.01,2.0),(False,True),(False,True)):
        top=object();parent=NS(children=.7) if with_parent else None
        hit=NS(top=top,calls=[0]*4,inclusive=[0.]*4,exclusive=[0.]*4)
        saved=[];e=dict(hit=hit,previous=parent,part=part,begin=100. if valid else 0.,children=children,
            GetLastError=lambda:123,SetLastError=lambda x:saved.append(x),_finite=math.isfinite)
        e['IrisDiagnostics::Now']=lambda: (100.+elapsed if valid else elapsed);e['std::max']=max
        p.statement(body,e)
        assert hit.top is parent and saved==[123]
        assert hit.calls[part]==int(valid)
        assert hit.inclusive[part]==(elapsed if valid else 0.) or math.isclose(hit.inclusive[part],elapsed)
        assert math.isclose(hit.exclusive[part],max(0.,elapsed-children) if valid else 0.)
        if parent:assert math.isclose(parent.children,.7+elapsed if valid else .7)
        count+=1
    return {'actual_PartScope_destructor_AST_cases':count,'parent_stack_restored':True,'exclusive_children_subtracted':True,'LastError_preserved':True}

def switches_and_observation(p,a):
    count=0
    for option,details,tls in itertools.product((False,True),repeat=3):
        e=dict(nativeOption=option,serviceOption=option,hitTLS=0 if tls else 0xffffffff,frameTLS=0 if tls else 0xffffffff,TLS_OUT_OF_INDEXES=0xffffffff)
        e['IrisDiagnostics::DetailsEnabled']=lambda:details
        assert p.execute(p.body('Enabled'),e)==(option and details and tls)
        assert p.execute(p.body('ServiceEnabled'),e)==(option and details and tls);count+=2
    # AST首个短路门确实在时钟/TLS/引擎访问前；运行该门应直接return。
    guards=[(p,definitions(p,'Hit'),{'Enabled':lambda:False}),
            (p,definitions(p,'PartScope'),{'Enabled':lambda:False}),
            (p,definitions(p,'Frame'),{'ServiceEnabled':lambda:False}),
            (Program(a),Program(a).body('ObserveServiceOpportunity'),{'IrisNativeAudit::ServiceEnabled':lambda:False})]
    for prog,body,env in guards:
        first=next(n for n in body.named_children if n.type!='comment');assert first.type=='if_statement'
        try:prog.statement(first,env)
        except Returned:pass
        else:raise AssertionError('关闭未短路')
    cb=p.body('Callback');ready=next(n.child_by_field_name('value') for n in p.nodes('init_declarator') if p.txt(n.child_by_field_name('declarator'))=='ready')
    cases=0
    for missing,phy,ai,pause,failed in itertools.product((-1,0,1),(-1,0,1),(-1,0,1),(-1,0,1),(False,True)):
        state=NS(unavailable=missing,physicsRunning=phy,aiRunning=ai,paused=pause,failed=failed)
        result=p.expr(ready,dict(state=state));assert result==(not failed and missing==0 and phy==0 and ai==0 and pause==0);cases+=1
    observer=Program(a).txt(Program(a).body('ObserveServiceOpportunity'))
    assert 'queuesAreClearMT' not in observer and 'Flush(' not in observer
    return {'switch_AST_cases':count,'disabled_early_return_AST_cases':len(guards),'tri_state_ready_AST_cases':cases,'observer_does_not_query_or_flush':True}

def forwarders(p):
    records=[]
    for name,original,expected in (('WoundHook','originalWound',['self','low','dir','damage','material','attacker','direction','harpoon']),('EffectHook','originalEffect',['data','who','bone','position','rotation'])):
        b=p.body(name);calls=[n for n in p.nodes('call_expression') if n.start_byte>=b.start_byte and n.end_byte<=b.end_byte and p.txt(n.child_by_field_name('function'))==original]
        assert len(calls)==1
        assert [p.txt(n) for n in calls[0].child_by_field_name('arguments').named_children]==expected
        for i in range(32):
            objects=[NS(value=i+j) for j in range(len(expected))];trace=[];result=object()
            def fn(*args):trace.append(args);return result
            e=dict(zip(expected,objects));e[original]=fn
            actual=p.expr(calls[0],e);assert actual is result and len(trace)==1 and all(a is b for a,b in zip(trace[0],objects))
        records.append(name)
    return {'actual_forwarding_call_AST_cases':64,'parameters_and_reference_identity_preserved':records,'return_value_untouched':True}

def lifecycle_specs():
    # 独立栈/TLS需求规格，非Windows线程执行：覆盖嵌套根不重叠、其他线程隔离和读档自然退栈。
    contexts={};generation=0;samples=[];nested=0
    for outer_thread in (1,2,3):
        owner={'generation':generation,'top':None};contexts[outer_thread]=owner
        assert contexts.get(99) is None
        nested+=1;assert contexts[outer_thread] is owner
        first={'previous':owner['top']};owner['top']=first
        second={'previous':owner['top']};owner['top']=second
        owner['top']=second['previous'];assert owner['top'] is first
        owner['top']=first['previous'];assert owner['top'] is None
        if outer_thread==2:generation+=1
        if owner['generation']==generation:samples.append(outer_thread)
        contexts[outer_thread]=None
    assert samples==[1,3] and not any(contexts.values()) and nested==3
    # FIFO预算需求规格来自既有083回放：长调用只完成一次，下一轮从最老剩余继续。
    return {'TLS_isolation_threads_modelled':4,'nested_roots_modelled':3,'generation_invalidated_scope_modelled':1,'real_thread_execution':False}

def main(before,out):
    a=(ROOT/'IrisArsenal.cpp').read_text('utf-8-sig');c=(ROOT/'IrisCombat.cpp').read_text('utf-8-sig');d=(ROOT/'IrisDiagnostics.cpp').read_text('utf-8-sig');n=(ROOT/'IrisNativeAudit.cpp').read_text('utf-8-sig');p=Eval(n)
    result={'flow':preserve(before,a,c,d),'individual_histogram':histogram(p),'nested_parts':parts(p),'disabled_and_tri_state':switches_and_observation(p,a),'forwarding':forwarders(p),'lifecycle_specs':lifecycle_specs()}
    old=(before/'IrisCombat.cpp').read_text('utf-8-sig');gates=0
    for bits in itertools.product((False,True),repeat=10):
        x,xt=condition_case(old,bits);y,yt=condition_case(c,bits);assert vars(x)==vars(y) and xt==yt;gates+=1
    result['actual_medical_gate_AST_cases']=gates;result['retained_reentry_FIFO_and_budget_specs']=replay(c);result['retained_window_ready_AST']=ready_cases(d)
    from test_capsule_policy081 import check_shadow,check_storage,check_geometry
    nc=(ROOT/'native/NativeMultiContact.cpp').read_text('utf-8-sig');result['retained_collision081']={'shadow':check_shadow(c),'storage':check_storage(nc),'geometry':check_geometry(nc)}
    for config in ('distribution/IrisArsenal.ini','package/IrisArsenal/IrisArsenal.ini'):
        before_ini,now=configparser.ConfigParser(),configparser.ConfigParser();before_ini.read(before/config,encoding='utf-8-sig');now.read(ROOT/config,encoding='utf-8-sig')
        for key in ('EnableNativeHitProfiling','EnableServiceOpportunityLogging'):assert now.getint('IrisArsenal',key)==1;now.remove_option('IrisArsenal',key)
        assert {x:dict(now[x]) for x in now.sections()}=={x:dict(before_ini[x]) for x in before_ini.sections()}
    syntax=[]
    for f in list(ROOT.glob('*.cpp'))+list(ROOT.glob('*.h'))+list((ROOT/'native').glob('*.cpp'))+list((ROOT/'native').glob('*.h')):
        Program(re.sub(r'__declspec\((?:[^()]|\([^()]*\))*\)','',f.read_text('utf-8-sig')));syntax.append(f.relative_to(ROOT).as_posix())
    for f in ('tools/stage_package.py','tools/test_update_mod.py','tools/test_native_profile084.py'):ast.parse((ROOT/f).read_text('utf-8-sig'))
    from stage_package import validate_dll
    try:validate_dll()
    except RuntimeError as e:assert '084原生受击/服务机会诊断' in str(e);result['old_DLL_rejected']=str(e)
    else:raise AssertionError('旧DLL不得冒充084')
    project=(ROOT/'IrisArsenal.vcxproj').read_text('utf-8-sig');assert '<ClCompile Include="IrisNativeAudit.cpp"' in project and '<ClInclude Include="IrisNativeAudit.h"' in project
    assert 'std::uncaught_exception()' in n and 'TlsFree(' not in n and 'new ' not in re.sub(r'//[^\n]*','',n)
    assert n.count('KenshiLib::AddHook(')==2 and 'if(Enabled()){' in n
    result.update(syntax_checked=syntax,original_ini_values_preserved=True,compiled=False,game_or_PhysX_or_thread_tested=False,FPS_measured=False,validation='实际源码AST与纯值规格，不代替用户MSVC编译/游戏测试')
    with out.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':
    q=argparse.ArgumentParser();q.add_argument('--before',type=Path,required=True);q.add_argument('--out',type=Path,required=True);x=q.parse_args();main(x.before,x.out)
